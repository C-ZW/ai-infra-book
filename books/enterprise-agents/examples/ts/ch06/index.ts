import { OrderOpsMockBackend } from "../shared/orderops-mock.js";
import type { RefundResult } from "../shared/types.js";

export type RunStatus =
  | "running"
  | "waiting_hitl"
  | "completed"
  | "escalated"
  | "failed";

export interface CheckpointEvent {
  runId: string;
  seq: number;
  stepType: "llm_turn" | "tool_call" | "hitl_pause" | "hitl_resume" | "completed" | "failed";
  payload: Record<string, unknown>;
  createdAt: string;
}

export class InMemoryCheckpointStore {
  private events: CheckpointEvent[] = [];

  append(event: Omit<CheckpointEvent, "seq" | "createdAt">): CheckpointEvent {
    const seq = this.events.filter((e) => e.runId === event.runId).length + 1;
    const record: CheckpointEvent = {
      ...event,
      seq,
      createdAt: new Date().toISOString(),
    };
    this.events.push(record);
    return record;
  }

  getEvents(runId: string): CheckpointEvent[] {
    return this.events
      .filter((e) => e.runId === runId)
      .sort((a, b) => a.seq - b.seq);
  }
}

export class RetryableApiError extends Error {
  constructor(
    message: string,
    public readonly statusCode: 429 | 529,
    public readonly retryAfterSec?: number,
  ) {
    super(message);
    this.name = "RetryableApiError";
  }
}

export async function withBackoffAndJitter<T>(
  fn: () => Promise<T>,
  options: { maxAttempts?: number; baseDelayMs?: number; maxDelayMs?: number } = {},
): Promise<T> {
  const maxAttempts = options.maxAttempts ?? 4;
  const baseDelayMs = options.baseDelayMs ?? 50;
  const maxDelayMs = options.maxDelayMs ?? 1000;

  let lastError: unknown;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (err) {
      lastError = err;
      if (!(err instanceof RetryableApiError) || attempt === maxAttempts) {
        throw err;
      }
      const expCap = Math.min(maxDelayMs, baseDelayMs * 2 ** (attempt - 1));
      const fullJitterMs = Math.floor(Math.random() * expCap);
      const retryAfterMs = err.retryAfterSec ? err.retryAfterSec * 1000 : 0;
      const delayMs = Math.max(fullJitterMs, retryAfterMs);
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }
  throw lastError;
}

export class CircuitBreaker {
  private state: "closed" | "open" | "half_open" = "closed";
  private failures = 0;
  private openedAt = 0;
  private epoch = 0;
  private halfOpenInFlight = false;

  constructor(
    private readonly failureThreshold = 3,
    private readonly cooldownMs = 200,
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === "open") {
      if (Date.now() - this.openedAt >= this.cooldownMs) {
        this.state = "half_open";
        this.halfOpenInFlight = false;
      } else {
        throw new Error("CircuitBreaker is OPEN; failing fast");
      }
    }

    if (this.state === "half_open") {
      if (this.halfOpenInFlight) {
        throw new Error("CircuitBreaker is HALF_OPEN; probe in flight");
      }
      this.halfOpenInFlight = true;
    }

    const callEpoch = this.epoch;
    try {
      const result = await fn();
      if (callEpoch === this.epoch) {
        this.failures = 0;
        this.state = "closed";
        this.halfOpenInFlight = false;
      }
      return result;
    } catch (err) {
      if (err instanceof RetryableApiError && callEpoch === this.epoch) {
        this.failures += 1;
        this.halfOpenInFlight = false;
        if (this.state === "half_open" || this.failures >= this.failureThreshold) {
          this.state = "open";
          this.openedAt = Date.now();
          this.epoch += 1;
        }
      } else if (callEpoch === this.epoch) {
        this.halfOpenInFlight = false;
      }
      throw err;
    }
  }

  getState(): string {
    return this.state;
  }
}

export class DurableOrderOpsRunner {
  private readonly store = new InMemoryCheckpointStore();
  private readonly backend = new OrderOpsMockBackend();
  private readonly breaker = new CircuitBreaker(3, 150);

  async runRefundWorkflow(params: {
    runId: string;
    refundOperationId: string;
    orderId: string;
    tenantId: string;
    amountUsd: number;
    reason: string;
  }): Promise<{ status: RunStatus; result?: RefundResult; events: CheckpointEvent[] }> {
    if (!Number.isFinite(params.amountUsd) || params.amountUsd <= 0) {
      throw new Error("amountUsd must be a positive finite number");
    }
    const idempotencyKey = `${params.tenantId}:${params.refundOperationId}`;

    const existing = this.store.getEvents(params.runId);
    const completed = existing.find((e) => e.stepType === "completed");
    if (completed) {
      return {
        status: "completed",
        result: completed.payload.refund as RefundResult | undefined,
        events: existing,
      };
    }

    const paused = existing.find((e) => e.stepType === "hitl_pause");
    const resumed = existing.find((e) => e.stepType === "hitl_resume");

    if (!paused) {
      const hasLlmTurn = existing.some((e) => e.stepType === "llm_turn");
      if (!hasLlmTurn) {
        let apiAttempts = 0;
        const llmDecision = await this.breaker.execute(() =>
          withBackoffAndJitter(async () => {
            apiAttempts += 1;
            if (apiAttempts === 1) {
              throw new RetryableApiError("Rate limit exceeded", 429, 0.02);
            }
            return { action: "issue_refund", amountUsd: params.amountUsd };
          }),
        );

        this.store.append({
          runId: params.runId,
          stepType: "llm_turn",
          payload: { decision: llmDecision, apiAttempts },
        });
      }

      const refund = this.backend.issueRefund({
        orderId: params.orderId,
        tenantId: params.tenantId,
        amountUsd: params.amountUsd,
        reason: params.reason,
        idempotencyKey,
        autoApproveLimitUsd: 250.0,
      });

      this.store.append({
        runId: params.runId,
        stepType: "tool_call",
        payload: { tool: "issue_refund", idempotencyKey, refund },
      });

      if (refund.status === "pending_hitl") {
        this.store.append({
          runId: params.runId,
          stepType: "hitl_pause",
          payload: { reason: refund.reason, deadlineSec: 3600 },
        });
        return {
          status: "waiting_hitl",
          result: refund,
          events: this.store.getEvents(params.runId),
        };
      }

      const terminalStep = refund.status === "rejected" ? "failed" : "completed";
      this.store.append({
        runId: params.runId,
        stepType: terminalStep,
        payload: { refund },
      });
      return {
        status: terminalStep,
        result: refund,
        events: this.store.getEvents(params.runId),
      };
    }

    if (paused && !resumed) {
      return {
        status: "waiting_hitl",
        events: existing,
      };
    }

    const approvedRefund = this.backend.issueRefund({
      orderId: params.orderId,
      tenantId: params.tenantId,
      amountUsd: params.amountUsd,
      reason: params.reason,
      idempotencyKey: `${idempotencyKey}:approved`,
      autoApproveLimitUsd: 10000.0,
    });

    this.store.append({
      runId: params.runId,
      stepType: "tool_call",
      payload: { tool: "issue_refund", idempotencyKey: `${idempotencyKey}:approved`, refund: approvedRefund },
    });
    this.store.append({
      runId: params.runId,
      stepType: "completed",
      payload: { refund: approvedRefund },
    });

    return {
      status: "completed",
      result: approvedRefund,
      events: this.store.getEvents(params.runId),
    };
  }

  approveHitl(runId: string, approver: string): CheckpointEvent[] {
    const existing = this.store.getEvents(runId);
    const isWaiting =
      existing.some((e) => e.stepType === "hitl_pause") &&
      !existing.some((e) => e.stepType === "hitl_resume" || e.stepType === "completed" || e.stepType === "failed");
    if (!isWaiting) {
      throw new Error(`Run ${runId} is not waiting for HITL approval`);
    }
    this.store.append({
      runId,
      stepType: "hitl_resume",
      payload: { approved: true, approver },
    });
    return this.store.getEvents(runId);
  }
}

async function main(): Promise<void> {
  const runner = new DurableOrderOpsRunner();

  // ORD-2026-88412 totalUsd is 340.0; requesting $300.0 triggers HITL (> $250 auto-approve limit)
  const firstPass = await runner.runRefundWorkflow({
    runId: "run-ch06-001",
    refundOperationId: "op-refund-9001",
    orderId: "ORD-2026-88412",
    tenantId: "tenant-apac-01",
    amountUsd: 300.0,
    reason: "Carrier delay SLA compensation",
  });

  console.log("First pass status:", firstPass.status);
  console.log("Checkpoints recorded:", firstPass.events.length);

  // Simulate human approval arriving later, then resume the workflow
  runner.approveHitl("run-ch06-001", "ops-lead@example.com");
  const resumedPass = await runner.runRefundWorkflow({
    runId: "run-ch06-001",
    refundOperationId: "op-refund-9001",
    orderId: "ORD-2026-88412",
    tenantId: "tenant-apac-01",
    amountUsd: 300.0,
    reason: "Carrier delay SLA compensation",
  });
  console.log("After HITL approval, total checkpoints:", resumedPass.events.length);
  console.log("Final step:", resumedPass.events[resumedPass.events.length - 1]?.stepType);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
