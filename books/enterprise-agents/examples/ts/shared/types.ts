export type TicketPriority = "low" | "medium" | "high" | "critical";

export type TicketCategory =
  | "shipping_delay"
  | "inventory_mismatch"
  | "refund_request"
  | "invoice_discrepancy"
  | "sla_breach";

export interface OrderOpsTicket {
  ticketId: string;
  tenantId: string;
  customerId: string;
  orderId: string;
  category: TicketCategory;
  priority: TicketPriority;
  subject: string;
  body: string;
  createdAt: string;
}

export interface OrderRecord {
  orderId: string;
  tenantId: string;
  customerId: string;
  status: "processing" | "shipped" | "delayed" | "delivered" | "refunded";
  totalUsd: number;
  currency: "USD";
  items: Array<{ sku: string; qty: number; unitPriceUsd: number }>;
  carrierTracking?: string;
  promisedDeliveryDate: string;
}

export interface RefundResult {
  refundId: string;
  orderId: string;
  amountUsd: number;
  idempotencyKey: string;
  status: "approved" | "pending_hitl" | "rejected";
  reason?: string;
}

export interface ModelPricing {
  inputPerMTok: number;
  outputPerMTok: number;
  cacheWrite5mMultiplier: number;
  cacheWrite1hMultiplier: number;
  cacheReadMultiplier: number;
}

export const CLAUDE_PRICING_2026_11: Record<string, ModelPricing> = {
  "claude-haiku-5-5": {
    inputPerMTok: 0.1,
    outputPerMTok: 0.5,
    cacheWrite5mMultiplier: 1.25,
    cacheWrite1hMultiplier: 2.0,
    cacheReadMultiplier: 0.1,
  },
  "claude-sonnet-5-5": {
    inputPerMTok: 2.0,
    outputPerMTok: 10.0,
    cacheWrite5mMultiplier: 1.25,
    cacheWrite1hMultiplier: 2.0,
    cacheReadMultiplier: 0.05,
  },
  "claude-opus-5-5": {
    inputPerMTok: 4.0,
    outputPerMTok: 20.0,
    cacheWrite5mMultiplier: 1.25,
    cacheWrite1hMultiplier: 2.0,
    cacheReadMultiplier: 0.05,
  },
};

export function calculateCostUsd(
  model: string,
  usage: {
    input_tokens: number;
    output_tokens: number;
    cache_creation_input_tokens?: number | null;
    cache_read_input_tokens?: number | null;
  },
  ttl: "5m" | "1h" = "5m",
): number {
  const p = CLAUDE_PRICING_2026_11[model] ?? CLAUDE_PRICING_2026_11["claude-sonnet-5-5"];
  const writeMult = ttl === "1h" ? p.cacheWrite1hMultiplier : p.cacheWrite5mMultiplier;
  const cacheCreate = usage.cache_creation_input_tokens ?? 0;
  const cacheRead = usage.cache_read_input_tokens ?? 0;
  return (
    (usage.input_tokens * p.inputPerMTok) / 1_000_000 +
    (usage.output_tokens * p.outputPerMTok) / 1_000_000 +
    (cacheCreate * p.inputPerMTok * writeMult) / 1_000_000 +
    (cacheRead * p.inputPerMTok * p.cacheReadMultiplier) / 1_000_000
  );
}
