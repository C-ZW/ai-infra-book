import { calculateCostUsd, type OrderOpsTicket } from "../shared/types.js";

export type SpanKind = "agent.request" | "agent.turn" | "gen_ai.client" | "agent.tool";

export type SpanAttrValue = string | number | boolean | string[];

export interface TelemetrySpan {
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  name: string;
  kind: SpanKind;
  startTimeMs: number;
  endTimeMs: number;
  status: "OK" | "ERROR";
  attributes: Record<string, SpanAttrValue>;
}

export class AgentTracer {
  private spans: TelemetrySpan[] = [];
  private seq = 0;

  startSpan(
    traceId: string,
    name: string,
    kind: SpanKind,
    attributes: Record<string, SpanAttrValue>,
    parentSpanId?: string,
  ): TelemetrySpan {
    this.seq += 1;
    const span: TelemetrySpan = {
      traceId,
      spanId: `span-${String(this.seq).padStart(4, "0")}`,
      parentSpanId,
      name,
      kind,
      startTimeMs: Date.now(),
      endTimeMs: 0,
      status: "OK",
      attributes: { ...attributes },
    };
    this.spans.push(span);
    return span;
  }

  endSpan(span: TelemetrySpan, status: "OK" | "ERROR" = "OK", extra?: Record<string, SpanAttrValue>): void {
    span.endTimeMs = Date.now();
    span.status = status;
    if (extra) {
      Object.assign(span.attributes, extra);
    }
  }

  getTrace(traceId: string): TelemetrySpan[] {
    return this.spans.filter((s) => s.traceId === traceId);
  }
}

export interface BudgetConfig {
  maxTicketCostUsd: number;
  maxHourlyBurnUsd: number;
}

export class BudgetCircuitBreaker {
  private hourlyBurnUsd = 0;
  private windowStartMs = Date.now();
  private tripped = false;

  constructor(private readonly config: BudgetConfig) {}

  private resetWindowIfNeeded(now: number): void {
    if (now - this.windowStartMs >= 3_600_000) {
      this.hourlyBurnUsd = 0;
      this.windowStartMs = now;
      this.tripped = false;
    }
  }

  checkBeforeSend(ticketCostUsd: number): { allowed: boolean; reason?: string } {
    this.resetWindowIfNeeded(Date.now());
    if (this.tripped || this.hourlyBurnUsd >= this.config.maxHourlyBurnUsd) {
      this.tripped = true;
      return { allowed: false, reason: "CIRCUIT_OPEN_HOURLY_CAP" };
    }
    if (ticketCostUsd >= this.config.maxTicketCostUsd) {
      return {
        allowed: false,
        reason: `TICKET_BUDGET_EXCEEDED ($${ticketCostUsd.toFixed(4)} >= $${this.config.maxTicketCostUsd.toFixed(2)})`,
      };
    }
    return { allowed: true };
  }

  recordUsage(ticketCostUsd: number, turnCostUsd: number): { allowed: boolean; reason?: string } {
    this.resetWindowIfNeeded(Date.now());
    this.hourlyBurnUsd += turnCostUsd;

    if (ticketCostUsd + turnCostUsd > this.config.maxTicketCostUsd) {
      return {
        allowed: false,
        reason: `TICKET_BUDGET_EXCEEDED ($${(ticketCostUsd + turnCostUsd).toFixed(4)} > $${this.config.maxTicketCostUsd.toFixed(2)})`,
      };
    }

    if (this.hourlyBurnUsd > this.config.maxHourlyBurnUsd) {
      this.tripped = true;
      return {
        allowed: false,
        reason: `HOURLY_BURN_EXCEEDED ($${this.hourlyBurnUsd.toFixed(2)} > $${this.config.maxHourlyBurnUsd.toFixed(2)})`,
      };
    }

    return { allowed: true };
  }
}

export type StopReason =
  | "end_turn"
  | "tool_use"
  | "max_tokens"
  | "refusal"
  | "stop_sequence"
  | "pause_turn"
  | "model_context_window_exceeded"
  | (string & {});

export interface UsagePayload {
  model: string;
  input_tokens: number;
  output_tokens: number;
  cache_creation_input_tokens: number;
  cache_read_input_tokens: number;
  stop_reason: StopReason | null;
}

export function runObservedTurn(
  tracer: AgentTracer,
  breaker: BudgetCircuitBreaker,
  ticket: OrderOpsTicket,
  traceId: string,
  rootSpanId: string,
  turnIndex: number,
  ticketCostSoFar: number,
  usage: UsagePayload,
): { turnCostUsd: number; cacheHitRatio: number; blockedReason?: string } {
  const turnSpan = tracer.startSpan(
    traceId,
    `turn.${turnIndex}`,
    "agent.turn",
    {
      "agent.turn_index": turnIndex,
      "agent.tenant_id": ticket.tenantId,
      "agent.ticket_category": ticket.category,
    },
    rootSpanId,
  );

  const preGuard = breaker.checkBeforeSend(ticketCostSoFar);
  if (!preGuard.allowed) {
    tracer.endSpan(turnSpan, "ERROR", { "agent.abort_reason": preGuard.reason ?? "CIRCUIT_OPEN" });
    return { turnCostUsd: 0, cacheHitRatio: 0, blockedReason: preGuard.reason };
  }

  const totalInput = usage.input_tokens + usage.cache_creation_input_tokens + usage.cache_read_input_tokens;
  const llmSpan = tracer.startSpan(
    traceId,
    `anthropic.messages.create`,
    "gen_ai.client",
    {
      "gen_ai.provider.name": "anthropic",
      "gen_ai.operation.name": "chat",
      "gen_ai.request.model": usage.model,
      "gen_ai.usage.input_tokens": totalInput,
      "gen_ai.usage.output_tokens": usage.output_tokens,
      "gen_ai.usage.cache_creation.input_tokens": usage.cache_creation_input_tokens,
      "gen_ai.usage.cache_read.input_tokens": usage.cache_read_input_tokens,
      "gen_ai.response.finish_reasons": usage.stop_reason ? [usage.stop_reason] : [],
    },
    turnSpan.spanId,
  );

  const turnCostUsd = calculateCostUsd(usage.model, usage, "5m");
  const cacheHitRatio = totalInput > 0 ? usage.cache_read_input_tokens / totalInput : 0;

  tracer.endSpan(llmSpan, "OK", {
    "agent.cost_usd": Number(turnCostUsd.toFixed(6)),
    "agent.cache_hit_ratio": Number(cacheHitRatio.toFixed(4)),
  });

  if (usage.stop_reason === "tool_use") {
    const toolSpan = tracer.startSpan(
      traceId,
      "tool.lookup_order",
      "agent.tool",
      { "agent.tool_name": "lookup_order", "agent.is_error": false },
      turnSpan.spanId,
    );
    tracer.endSpan(toolSpan, "OK");
  }

  const postGuard = breaker.recordUsage(ticketCostSoFar, turnCostUsd);
  if (!postGuard.allowed) {
    tracer.endSpan(turnSpan, "ERROR", { "agent.abort_reason": postGuard.reason ?? "BUDGET_EXCEEDED" });
    return { turnCostUsd, cacheHitRatio, blockedReason: postGuard.reason };
  }

  tracer.endSpan(turnSpan, "OK");
  return { turnCostUsd, cacheHitRatio };
}

function main(): void {
  const tracer = new AgentTracer();
  const breaker = new BudgetCircuitBreaker({ maxTicketCostUsd: 0.15, maxHourlyBurnUsd: 25.0 });

  const ticket: OrderOpsTicket = {
    ticketId: "TKT-10492",
    tenantId: "tenant-acme",
    customerId: "cust-881",
    orderId: "ORD-7721",
    category: "refund_request",
    priority: "high",
    subject: "Delayed shipment refund",
    body: "Order delayed 5 days past promised date.",
    createdAt: "2026-11-21T10:00:00Z",
  };

  const traceId = "trace-orderops-10492";
  const rootSpan = tracer.startSpan(traceId, "orderops.handle_ticket", "agent.request", {
    "agent.ticket_id": ticket.ticketId,
    "agent.tenant_id": ticket.tenantId,
  });

  // Scenario 1: Healthy cached turn (85% cache hit)
  const r1 = runObservedTurn(tracer, breaker, ticket, traceId, rootSpan.spanId, 1, 0, {
    model: "claude-sonnet-5-5",
    input_tokens: 1200,
    output_tokens: 350,
    cache_creation_input_tokens: 0,
    cache_read_input_tokens: 6800,
    stop_reason: "tool_use",
  });

  // Scenario 2: Cache silent miss (0% cache hit, prefix invalidated)
  const r2 = runObservedTurn(tracer, breaker, ticket, traceId, rootSpan.spanId, 2, r1.turnCostUsd, {
    model: "claude-sonnet-5-5",
    input_tokens: 8000,
    output_tokens: 350,
    cache_creation_input_tokens: 0,
    cache_read_input_tokens: 0,
    stop_reason: "end_turn",
  });

  const blocked = Boolean(r1.blockedReason || r2.blockedReason);
  tracer.endSpan(rootSpan, blocked ? "ERROR" : "OK", {
    "agent.total_cost_usd": Number((r1.turnCostUsd + r2.turnCostUsd).toFixed(6)),
  });

  console.log("=== OrderOps Telemetry Summary ===");
  console.log(`Turn 1 (cached): cost=$${r1.turnCostUsd.toFixed(5)}, cache_hit=${(r1.cacheHitRatio * 100).toFixed(1)}%`);
  console.log(`Turn 2 (cache miss): cost=$${r2.turnCostUsd.toFixed(5)}, cache_hit=${(r2.cacheHitRatio * 100).toFixed(1)}%`);
  console.log(`Total spans recorded: ${tracer.getTrace(traceId).length}`);
}

main();
