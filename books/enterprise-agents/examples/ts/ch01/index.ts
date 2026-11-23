import Anthropic from "@anthropic-ai/sdk";
import type {
  MessageParam,
  Tool,
  ToolResultBlockParam,
  ToolUseBlock,
} from "@anthropic-ai/sdk/resources/messages.js";
import { OrderOpsMockBackend } from "../shared/orderops-mock.js";
import { calculateCostUsd, type OrderOpsTicket } from "../shared/types.js";

export interface AgentBudget {
  maxTurns: number;
  maxTotalInputTokens: number;
  maxCostUsd: number;
  wallClockTimeoutMs: number;
  turnTimeoutMs: number;
}

export interface AgentRunResult {
  status: "completed" | "budget_exceeded" | "timeout" | "refused" | "error";
  finalText: string;
  turns: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  totalCostUsd: number;
  stopReason: string;
}

const DEFAULT_BUDGET: AgentBudget = {
  maxTurns: 8,
  maxTotalInputTokens: 50_000,
  maxCostUsd: 0.25,
  wallClockTimeoutMs: 18_000, // OrderOps multi-step p95 SLO
  turnTimeoutMs: 5_000,
};

const TOOLS: Tool[] = [
  {
    name: "get_order",
    description: "Fetch order details by orderId and tenantId.",
    input_schema: {
      type: "object",
      properties: {
        order_id: { type: "string" },
        tenant_id: { type: "string" },
      },
      required: ["order_id", "tenant_id"],
    },
  },
  {
    name: "check_inventory",
    description: "Check warehouse inventory for a given SKU.",
    input_schema: {
      type: "object",
      properties: {
        sku: { type: "string" },
      },
      required: ["sku"],
    },
  },
  {
    name: "issue_refund",
    description: "Issue a refund for an order with an idempotency key.",
    input_schema: {
      type: "object",
      properties: {
        order_id: { type: "string" },
        tenant_id: { type: "string" },
        amount_usd: { type: "number" },
        reason: { type: "string" },
        idempotency_key: { type: "string" },
      },
      required: ["order_id", "tenant_id", "amount_usd", "reason", "idempotency_key"],
    },
  },
];

function executeTool(
  backend: OrderOpsMockBackend,
  ticket: OrderOpsTicket,
  block: ToolUseBlock,
): ToolResultBlockParam {
  const input = block.input as Record<string, unknown>;
  try {
    let output: unknown;
    switch (block.name) {
      case "get_order": {
        const orderId = typeof input.order_id === "string" ? input.order_id : "";
        if (!orderId) throw new Error("order_id must be a non-empty string");
        // Bind tenantId from authenticated ticket context, never trust model-supplied tenant_id
        output = backend.getOrder(orderId, ticket.tenantId);
        break;
      }
      case "check_inventory": {
        const sku = typeof input.sku === "string" ? input.sku : "";
        if (!sku) throw new Error("sku must be a non-empty string");
        output = backend.checkInventory(sku);
        break;
      }
      case "issue_refund": {
        const orderId = typeof input.order_id === "string" ? input.order_id : "";
        const amountUsd = typeof input.amount_usd === "number" ? input.amount_usd : Number.NaN;
        const reason = typeof input.reason === "string" ? input.reason : "";
        if (!orderId || !reason) throw new Error("order_id and reason must be non-empty strings");
        if (!Number.isFinite(amountUsd) || amountUsd <= 0) {
          throw new Error("amount_usd must be a finite positive number");
        }
        // Backend-derived tenantId and idempotencyKey prevent cross-tenant or key-collision abuse
        const idempotencyKey = `refund:${ticket.tenantId}:${ticket.ticketId}:${orderId}`;
        output = backend.issueRefund({
          orderId,
          tenantId: ticket.tenantId,
          amountUsd,
          reason,
          idempotencyKey,
        });
        break;
      }
      default:
        return {
          type: "tool_result",
          tool_use_id: block.id,
          content: JSON.stringify({ error: `Unknown tool: ${block.name}` }),
          is_error: true,
        };
    }
    return {
      type: "tool_result",
      tool_use_id: block.id,
      content: JSON.stringify(output),
    };
  } catch (err) {
    return {
      type: "tool_result",
      tool_use_id: block.id,
      content: JSON.stringify({
        error: err instanceof Error ? err.message : "Tool execution failed",
      }),
      is_error: true,
    };
  }
}

export async function runOrderOpsAgent(
  client: Anthropic,
  ticket: OrderOpsTicket,
  budget: AgentBudget = DEFAULT_BUDGET,
  model = "claude-sonnet-5-5",
): Promise<AgentRunResult> {
  const backend = new OrderOpsMockBackend();
  const startedAt = Date.now();
  const messages: MessageParam[] = [
    {
      role: "user",
      content: JSON.stringify(ticket),
    },
  ];

  let turns = 0;
  let totalInputTokens = 0;
  let totalOutputTokens = 0;
  let totalCostUsd = 0;

  while (turns < budget.maxTurns) {
    const elapsedMs = Date.now() - startedAt;
    if (elapsedMs >= budget.wallClockTimeoutMs) {
      return {
        status: "timeout",
        finalText: `Aborted: wall-clock timeout (${budget.wallClockTimeoutMs}ms) reached.`,
        turns,
        totalInputTokens,
        totalOutputTokens,
        totalCostUsd,
        stopReason: "wall_clock_timeout",
      };
    }

    turns += 1;
    const remainingMs = Math.min(budget.turnTimeoutMs, budget.wallClockTimeoutMs - elapsedMs);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), remainingMs);

    let response: Anthropic.Message;
    try {
      response = await client.messages.create(
        {
          model,
          max_tokens: 1024,
          system:
            "You are OrderOps Agent. Inspect the ticket, verify order/inventory state via tools, and resolve or escalate concisely.",
          tools: TOOLS,
          messages,
        },
        { signal: controller.signal },
      );
    } catch (err) {
      const postCallElapsedMs = Date.now() - startedAt;
      if (
        controller.signal.aborted ||
        err instanceof Anthropic.APIConnectionTimeoutError ||
        err instanceof Anthropic.APIUserAbortError
      ) {
        const isWallClock = postCallElapsedMs >= budget.wallClockTimeoutMs;
        return {
          status: "timeout",
          finalText: `Aborted: ${isWallClock ? "wall-clock" : "turn"} timeout reached.`,
          turns,
          totalInputTokens,
          totalOutputTokens,
          totalCostUsd,
          stopReason: isWallClock ? "wall_clock_timeout" : "turn_timeout",
        };
      }
      return {
        status: "error",
        finalText: `Aborted: API error (${err instanceof Error ? err.message : "unknown"})`,
        turns,
        totalInputTokens,
        totalOutputTokens,
        totalCostUsd,
        stopReason: "api_error",
      };
    } finally {
      clearTimeout(timer);
    }

    totalInputTokens += response.usage.input_tokens;
    totalOutputTokens += response.usage.output_tokens;
    totalCostUsd += calculateCostUsd(model, response.usage);

    if (totalInputTokens > budget.maxTotalInputTokens || totalCostUsd > budget.maxCostUsd) {
      return {
        status: "budget_exceeded",
        finalText: `Aborted: budget exceeded (tokens=${totalInputTokens}, cost=$${totalCostUsd.toFixed(4)}).`,
        turns,
        totalInputTokens,
        totalOutputTokens,
        totalCostUsd,
        stopReason: "budget_exceeded",
      };
    }

    messages.push({ role: "assistant", content: response.content });

    if (response.stop_reason === "end_turn") {
      const text = response.content
        .filter((b): b is Anthropic.TextBlock => b.type === "text")
        .map((b) => b.text)
        .join("\n");
      return {
        status: "completed",
        finalText: text,
        turns,
        totalInputTokens,
        totalOutputTokens,
        totalCostUsd,
        stopReason: "end_turn",
      };
    }

    if (response.stop_reason === "tool_use") {
      if (turns >= budget.maxTurns) {
        return {
          status: "budget_exceeded",
          finalText: `Aborted: reached maxTurns=${budget.maxTurns} before tool execution.`,
          turns,
          totalInputTokens,
          totalOutputTokens,
          totalCostUsd,
          stopReason: "max_turns",
        };
      }
      if (Date.now() - startedAt >= budget.wallClockTimeoutMs) {
        return {
          status: "timeout",
          finalText: `Aborted: wall-clock timeout (${budget.wallClockTimeoutMs}ms) reached before tool dispatch.`,
          turns,
          totalInputTokens,
          totalOutputTokens,
          totalCostUsd,
          stopReason: "wall_clock_timeout",
        };
      }
      const toolBlocks = response.content.filter(
        (b): b is ToolUseBlock => b.type === "tool_use",
      );
      const toolResults = toolBlocks.map((b) => executeTool(backend, ticket, b));
      messages.push({ role: "user", content: toolResults });
      continue;
    }

    if (response.stop_reason === "refusal") {
      return {
        status: "refused",
        finalText: "Model refused to process the request.",
        turns,
        totalInputTokens,
        totalOutputTokens,
        totalCostUsd,
        stopReason: "refusal",
      };
    }

    if (response.stop_reason === "max_tokens") {
      return {
        status: "error",
        finalText: "Aborted: single-turn output hit max_tokens.",
        turns,
        totalInputTokens,
        totalOutputTokens,
        totalCostUsd,
        stopReason: "max_tokens",
      };
    }

    return {
      status: "error",
      finalText: `Aborted: unhandled stop_reason=${response.stop_reason}`,
      turns,
      totalInputTokens,
      totalOutputTokens,
      totalCostUsd,
      stopReason: response.stop_reason ?? "unknown",
    };
  }

  return {
    status: "budget_exceeded",
    finalText: `Aborted: reached maxTurns=${budget.maxTurns}.`,
    turns,
    totalInputTokens,
    totalOutputTokens,
    totalCostUsd,
    stopReason: "max_turns",
  };
}

async function main(): Promise<void> {
  if (!process.env.ANTHROPIC_API_KEY) {
    console.log("ANTHROPIC_API_KEY not set; skipping live API call.");
    return;
  }

  const client = new Anthropic();
  const sampleTicket: OrderOpsTicket = {
    ticketId: "TKT-2026-10492",
    tenantId: "tenant-apac-01",
    customerId: "CUST-9012",
    orderId: "ORD-2026-88412",
    category: "shipping_delay",
    priority: "high",
    subject: "Order delayed past promised date",
    body: "Please check order ORD-2026-88412 status and inventory for SKU-IND-401.",
    createdAt: "2026-11-21T10:00:00Z",
  };

  const result = await runOrderOpsAgent(client, sampleTicket);
  console.log(JSON.stringify(result, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
