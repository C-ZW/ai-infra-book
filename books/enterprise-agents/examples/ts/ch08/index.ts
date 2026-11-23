import { pathToFileURL } from "node:url";
import {
  calculateCostUsd,
  type OrderOpsTicket,
  type TicketCategory,
} from "../shared/types.js";

export type ModelTier = "claude-haiku-5-5" | "claude-sonnet-5-5" | "claude-opus-5-5";

export interface RoutingDecision {
  model: ModelTier;
  reason: string;
  batchEligible: boolean;
}

export function routeTicket(ticket: OrderOpsTicket): RoutingDecision {
  if (ticket.priority === "critical" || ticket.category === "sla_breach") {
    return {
      model: "claude-opus-5-5",
      reason: "high_risk_escalation",
      batchEligible: false,
    };
  }

  if (ticket.category === "invoice_discrepancy" && ticket.priority === "low") {
    return {
      model: "claude-haiku-5-5",
      reason: "offline_reconciliation",
      batchEligible: true,
    };
  }

  if (ticket.priority === "low" || ticket.category === "shipping_delay") {
    return {
      model: "claude-haiku-5-5",
      reason: "standard_triage",
      batchEligible: false,
    };
  }

  return {
    model: "claude-sonnet-5-5",
    reason: "standard_workflow",
    batchEligible: false,
  };
}

export interface ToolSchema {
  name: string;
  description: string;
  input_schema: {
    type: "object";
    properties: Record<string, unknown>;
    required?: string[];
  };
}

export function buildCachedPrefixBlocks(
  systemPrompt: string,
  toolSchemas: ToolSchema[],
  ttl: "5m" | "1h" = "5m",
) {
  return {
    system: [
      {
        type: "text" as const,
        text: systemPrompt,
        cache_control: { type: "ephemeral" as const, ttl },
      },
    ],
    tools: toolSchemas.map((tool, idx) =>
      idx === toolSchemas.length - 1
        ? { ...tool, cache_control: { type: "ephemeral" as const, ttl } }
        : tool,
    ),
  };
}

export function selectToolsForCategory(
  category: TicketCategory,
  allTools: Array<{ name: string; group: "read" | "refund" | "invoice" | "shipping" }>,
) {
  const allowedGroups: Record<TicketCategory, string[]> = {
    shipping_delay: ["read", "shipping"],
    inventory_mismatch: ["read", "shipping"],
    refund_request: ["read", "refund"],
    invoice_discrepancy: ["read", "invoice"],
    sla_breach: ["read", "refund", "shipping"],
  };
  const groups = new Set(allowedGroups[category]);
  return allTools
    .filter((t) => groups.has(t.group))
    .sort((a, b) => a.name.localeCompare(b.name));
}

export function simulateOrderOpsWaterfall(
  ttl: "5m" | "1h" = "5m",
  inferenceGeo: "global" | "us" = "global",
) {
  const monthlyTickets = 1_500_000;
  const geoMultiplier = inferenceGeo === "us" ? 1.1 : 1.0;
  const baselinePerTicket = calculateCostUsd("claude-sonnet-5-5", {
    input_tokens: 42_000,
    output_tokens: 1_750,
  });

  const stage5Haiku =
    calculateCostUsd(
      "claude-haiku-5-5",
      {
        input_tokens: 4_500,
        output_tokens: 1_050,
        cache_creation_input_tokens: 1_350,
        cache_read_input_tokens: 12_150,
      },
      ttl,
    );
  const stage5Sonnet =
    calculateCostUsd(
      "claude-sonnet-5-5",
      {
        input_tokens: 4_500,
        output_tokens: 1_050,
        cache_creation_input_tokens: 1_350,
        cache_read_input_tokens: 12_150,
      },
      ttl,
    );
  const stage5Opus =
    calculateCostUsd(
      "claude-opus-5-5",
      {
        input_tokens: 4_500,
        output_tokens: 1_050,
        cache_creation_input_tokens: 1_350,
        cache_read_input_tokens: 12_150,
      },
      ttl,
    );

  const weighted =
    (0.6 * stage5Haiku + 0.35 * stage5Sonnet + 0.05 * stage5Opus) *
    0.85 *
    geoMultiplier;

  return {
    baselineMonthlyUsd: Math.round(baselinePerTicket * monthlyTickets),
    optimizedMonthlyUsd: Math.round(weighted * monthlyTickets),
    optimizedPerTicketUsd: Number(weighted.toFixed(6)),
    reductionPct: Number(
      (((baselinePerTicket - weighted) / baselinePerTicket) * 100).toFixed(1),
    ),
  };
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(process.argv[1]).href
) {
  const sampleTicket: OrderOpsTicket = {
    ticketId: "T-8001",
    tenantId: "tenant-acme",
    customerId: "cust-101",
    orderId: "ORD-9001",
    category: "shipping_delay",
    priority: "low",
    subject: "Package delayed 2 days",
    body: "Where is my order ORD-9001?",
    createdAt: "2026-11-21T10:00:00Z",
  };
  console.log("Routing decision:", routeTicket(sampleTicket));
  console.log("Waterfall summary:", simulateOrderOpsWaterfall());
}
