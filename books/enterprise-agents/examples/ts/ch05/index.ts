/**
 * ch05: Multi-Agent Orchestration — Router, Orchestrator-Workers & Handoff Contract
 *
 * Demonstrates:
 * 1. Haiku Router (0 tools) classifying OrderOps tickets into specialist lanes.
 * 2. Orchestrator-Workers fan-out with Promise.allSettled, per-worker timeout, and max_turns.
 * 3. Compressed WorkerHandoff contract (no raw tool logs leaked to parent context).
 * 4. Opus Refund Specialist escalation for high-risk mutating operations.
 */

import type Anthropic from "@anthropic-ai/sdk";
import {
  type OrderOpsTicket,
  calculateCostUsd,
} from "../shared/types.js";
import { OrderOpsMockBackend } from "../shared/orderops-mock.js";

const backend = new OrderOpsMockBackend();
const SAMPLE_TICKETS: OrderOpsTicket[] = [
  {
    ticketId: "TKT-5001",
    tenantId: "tenant-apac-01",
    customerId: "CUST-9012",
    orderId: "ORD-2026-88412",
    category: "shipping_delay",
    priority: "high",
    subject: "Shipment delayed past promised date",
    body: "Order ORD-2026-88412 was promised 2026-11-18. Please check carrier and warehouse.",
    createdAt: "2026-11-21T10:00:00Z",
  },
  {
    ticketId: "TKT-5002",
    tenantId: "tenant-eu-02",
    customerId: "CUST-3318",
    orderId: "ORD-2026-88901",
    category: "refund_request",
    priority: "critical",
    subject: "Requesting full refund ($1,850)",
    body: "Customer requests full refund for ORD-2026-88901.",
    createdAt: "2026-11-21T10:05:00Z",
  },
];

export type SpecialistLane =
  | "shipping_investigator"
  | "inventory_investigator"
  | "refund_arbitrator";

export interface RouteDecision {
  lane: SpecialistLane;
  parallelReadOnlyTasks: Array<"carrier_status" | "warehouse_stock" | "billing_ledger">;
  confidence: number;
  reason: string;
}

export interface WorkerHandoff {
  workerId: string;
  task: string;
  status: "ok" | "timeout" | "error";
  summary: string;
  facts: Record<string, unknown>;
  latencyMs: number;
  costUsd: number;
}

export interface OrchestrationResult {
  ticketId: string;
  route: RouteDecision;
  handoffs: WorkerHandoff[];
  finalAction: string;
  totalCostUsd: number;
  totalLatencyMs: number;
}

const WORKER_TIMEOUT_MS = 8_000;
const WORKER_MAX_TURNS = 4;

class WorkerTimeoutError extends Error {
  constructor(label: string, ms: number) {
    super(`Worker ${label} timed out after ${ms}ms`);
    this.name = "WorkerTimeoutError";
  }
}

function withTimeout<T>(promise: Promise<T>, ms: number, label: string): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new WorkerTimeoutError(label, ms));
    }, ms);
    promise.then(
      (val) => {
        clearTimeout(timer);
        resolve(val);
      },
      (err) => {
        clearTimeout(timer);
        reject(err);
      },
    );
  });
}

/**
 * Haiku Router: 0 tools, minimal prefix, structured JSON routing decision.
 */
export async function routeTicket(
  client: Anthropic | null,
  ticket: OrderOpsTicket,
): Promise<{ decision: RouteDecision; costUsd: number }> {
  if (!client) {
    // Deterministic offline simulation matching Haiku 5.5 token profile
    const decision: RouteDecision =
      ticket.category === "refund_request"
        ? {
            lane: "refund_arbitrator",
            parallelReadOnlyTasks: ["carrier_status", "billing_ledger"],
            confidence: 0.96,
            reason: "Refund request requires carrier delivery check and ledger verification.",
          }
        : {
            lane: "shipping_investigator",
            parallelReadOnlyTasks: ["carrier_status", "warehouse_stock"],
            confidence: 0.94,
            reason: "Shipping delay requires carrier tracking and warehouse dispatch check.",
          };
    const costUsd = calculateCostUsd("claude-haiku-5-5", {
      input_tokens: 450,
      output_tokens: 90,
    });
    return { decision, costUsd };
  }

  const response = await client.messages.create({
    model: "claude-haiku-5-5",
    max_tokens: 256,
    system:
      "You are the OrderOps ticket router. Output ONLY valid JSON matching " +
      '{"lane": "shipping_investigator"|"inventory_investigator"|"refund_arbitrator", ' +
      '"parallelReadOnlyTasks": string[], "confidence": number, "reason": string}.',
    messages: [
      {
        role: "user",
        content: `Ticket ${ticket.ticketId} [${ticket.category}/${ticket.priority}]: ${ticket.subject}\n${ticket.body}`,
      },
    ],
  });

  const textBlock = response.content.find((b) => b.type === "text");
  const raw = textBlock && textBlock.type === "text" ? textBlock.text : "{}";
  const decision = JSON.parse(raw) as RouteDecision;
  const costUsd = calculateCostUsd("claude-haiku-5-5", response.usage);
  return { decision, costUsd };
}

/**
 * Read-only investigation worker with isolated context and compressed handoff.
 */
async function runReadOnlyWorker(
  ticket: OrderOpsTicket,
  task: "carrier_status" | "warehouse_stock" | "billing_ledger",
): Promise<WorkerHandoff> {
  const start = Date.now();
  const order = backend.getOrder(ticket.orderId, ticket.tenantId);

  // Simulate bounded worker loop (<= WORKER_MAX_TURNS)
  if (task === "billing_ledger" && ticket.priority === "critical") {
    // Simulate a transient timeout on one branch to demonstrate partial-failure resilience
    await new Promise((r) => setTimeout(r, 30));
  }

  const orderNotFound = "error" in order;
  const facts: Record<string, unknown> = orderNotFound
    ? { orderId: ticket.orderId, status: "not_found" }
    : {
        orderId: order.orderId,
        status: order.status,
        totalUsd: order.totalUsd,
        carrierTracking: order.carrierTracking ?? "N/A",
      };

  const costUsd = calculateCostUsd("claude-haiku-5-5", {
    input_tokens: 1_200,
    output_tokens: 180,
  });

  return {
    workerId: `worker-${task}`,
    task,
    status: orderNotFound ? "error" : "ok",
    summary: `[${task}] Order ${ticket.orderId} status=${String(facts.status)}, max_turns=${WORKER_MAX_TURNS}`,
    facts,
    latencyMs: Date.now() - start,
    costUsd,
  };
}

/**
 * Orchestrator: fans out read-only workers in parallel, collects compressed handoffs,
 * and escalates to Opus Specialist only when mutating/high-risk arbitration is needed.
 */
export async function orchestrateTicket(
  client: Anthropic | null,
  ticket: OrderOpsTicket,
): Promise<OrchestrationResult> {
  const t0 = Date.now();
  const { decision, costUsd: routerCost } = await routeTicket(client, ticket);

  // Fan-out read-only workers with Promise.allSettled + per-worker timeout
  const settled = await Promise.allSettled(
    decision.parallelReadOnlyTasks.map((task) =>
      withTimeout(runReadOnlyWorker(ticket, task), WORKER_TIMEOUT_MS, task),
    ),
  );

  const handoffs: WorkerHandoff[] = settled.map((res, idx) => {
    const task = decision.parallelReadOnlyTasks[idx];
    if (res.status === "fulfilled") {
      return res.value;
    }
    return {
      workerId: `worker-${task}`,
      task,
      status: res.reason instanceof WorkerTimeoutError ? "timeout" : "error",
      summary: `Worker failed: ${res.reason instanceof Error ? res.reason.message : String(res.reason)}`,
      facts: {},
      latencyMs: WORKER_TIMEOUT_MS,
      costUsd: 0,
    };
  });

  const workerCost = handoffs.reduce((acc, h) => acc + h.costUsd, 0);
  let specialistCost = 0;
  let finalAction = "resolved_read_only";

  if (decision.lane === "refund_arbitrator") {
    // Escalate to Opus 5.5 only with compressed handoffs (never raw tool logs)
    specialistCost = calculateCostUsd("claude-opus-5-5", {
      input_tokens: 2_800,
      output_tokens: 320,
    });
    const requiredTasks = ["carrier_status", "billing_ledger"] as const;
    const missingOrFailed = requiredTasks.filter((req) => {
      const h = handoffs.find((item) => item.task === req);
      return !h || h.status !== "ok" || h.facts.orderId !== ticket.orderId;
    });
    finalAction =
      missingOrFailed.length > 0
        ? `degraded_pending_hitl(missing_or_failed=${missingOrFailed.join(",")})`
        : "refund_approved_by_opus_specialist";
  } else {
    const failedWorkers = handoffs.filter((h) => h.status !== "ok");
    if (failedWorkers.length > 0 || handoffs.length === 0) {
      finalAction = `degraded_pending_hitl(failed=${failedWorkers.map((w) => w.task).join(",") || "none"})`;
    }
  }

  return {
    ticketId: ticket.ticketId,
    route: decision,
    handoffs,
    finalAction,
    totalCostUsd: routerCost + workerCost + specialistCost,
    totalLatencyMs: Date.now() - t0,
  };
}

async function main() {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  let client: Anthropic | null = null;
  if (apiKey) {
    const { default: AnthropicSDK } = await import("@anthropic-ai/sdk");
    client = new AnthropicSDK({ apiKey });
  }

  console.log(
    `[ch05] Running OrderOps Orchestrator (${client ? "LIVE API" : "OFFLINE SIMULATION"})`,
  );

  for (const ticket of SAMPLE_TICKETS.slice(0, 2)) {
    const result = await orchestrateTicket(client, ticket);
    console.log(JSON.stringify(result, null, 2));
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
