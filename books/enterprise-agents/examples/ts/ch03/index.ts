import Anthropic from "@anthropic-ai/sdk";
import { calculateCostUsd, type OrderOpsTicket } from "../shared/types.js";

const SAMPLE_TICKET: OrderOpsTicket = {
  ticketId: "TKT-2026-0301",
  tenantId: "tenant-apac-01",
  customerId: "CUST-9012",
  orderId: "ORD-2026-88412",
  category: "shipping_delay",
  priority: "high",
  subject: "Order ORD-2026-88412 delayed past promised date",
  body: "Promised delivery was 2026-11-18, tracking TRK-99812344 has not updated.",
  createdAt: "2026-11-21T10:00:00Z",
};

const MODEL = "claude-sonnet-5-5";
const THINKING_BUDGET_TOKENS = 4000; // Ledger demo assumption for billed thinking tokens
const MAX_TOKENS = 8000;
const TOOL_RESULT_MAX_CHARS = 2400; // Rough estimate: ~600 tokens

function escapeXml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export interface LayeredPrompt {
  tools: Anthropic.Tool[];
  system: Anthropic.TextBlockParam[];
  messages: Anthropic.MessageParam[];
}

/**
 * Build a cache-friendly prompt in strict prefix order: tools -> system -> messages.
 * Static instructions and tool schemas stay at the front with cache_control breakpoints;
 * dynamic ticket payload is placed at the tail.
 */
export function buildLayeredPrompt(
  ticket: OrderOpsTicket,
  tools: Anthropic.Tool[],
  staticPolicyText: string,
): LayeredPrompt {
  // Put cache_control on the last tool so the entire tool array is cached as a prefix
  const cachedTools = tools.map((tool, idx) =>
    idx === tools.length - 1
      ? { ...tool, cache_control: { type: "ephemeral" as const } }
      : tool,
  );

  const system: Anthropic.TextBlockParam[] = [
    {
      type: "text",
      text: staticPolicyText,
      cache_control: { type: "ephemeral" },
    },
  ];

  const dynamicUserContent = `<ticket_context>
  <ticket_id>${escapeXml(ticket.ticketId)}</ticket_id>
  <tenant_id>${escapeXml(ticket.tenantId)}</tenant_id>
  <order_id>${escapeXml(ticket.orderId)}</order_id>
  <category>${escapeXml(ticket.category)}</category>
  <priority>${escapeXml(ticket.priority)}</priority>
  <created_at>${escapeXml(ticket.createdAt)}</created_at>
  <subject>${escapeXml(ticket.subject)}</subject>
  <body>${escapeXml(ticket.body)}</body>
</ticket_context>`;

  return {
    tools: cachedTools,
    system,
    messages: [{ role: "user", content: dynamicUserContent }],
  };
}

/**
 * Truncate oversized tool output (e.g., 8,000-token ERP logs) down to ~600 tokens
 * to prevent multiplicative input bloat across subsequent turns.
 */
export function truncateToolResult(rawOutput: string, maxChars = TOOL_RESULT_MAX_CHARS): string {
  if (rawOutput.length <= maxChars) return rawOutput;
  if (maxChars <= 0) return "";
  const headLen = Math.floor(maxChars * 0.7);
  const tailLen = Math.floor(maxChars * 0.2);
  const head = headLen > 0 ? rawOutput.slice(0, headLen) : "";
  const tail = tailLen > 0 ? rawOutput.slice(-tailLen) : "";
  const omitted = rawOutput.length - head.length - tail.length;
  const marker = `\n...[truncated ${omitted} chars]...\n`;
  if (head.length + tail.length + marker.length > maxChars) {
    return rawOutput.slice(0, maxChars);
  }
  return `${head}${marker}${tail}`;
}

/**
 * Compact conversation history after Turn 4 by summarizing older turns into a
 * structured scratchpad while preserving the latest 2 turns verbatim.
 */
function summarizeContent(content: Anthropic.MessageParam["content"]): string {
  if (typeof content === "string") return content.slice(0, 120);
  return content
    .map((block) => {
      if (block.type === "text") return block.text.slice(0, 80);
      if (block.type === "tool_use") return `[tool_use:${block.name}]`;
      if (block.type === "tool_result") return `[tool_result:${block.tool_use_id}]`;
      return `[${block.type}]`;
    })
    .join(" ");
}

export function compactHistory(
  messages: Anthropic.MessageParam[],
  keepRecentTurns = 2,
): Anthropic.MessageParam[] {
  const keepCount = keepRecentTurns * 2; // user + assistant pairs
  if (messages.length <= keepCount + 1) return messages;

  let splitIdx = messages.length - keepCount;
  // Avoid splitting an assistant tool_use from its following user tool_result
  while (splitIdx > 1 && messages[splitIdx]?.role === "user" && Array.isArray(messages[splitIdx].content)) {
    splitIdx -= 1;
  }
  if (splitIdx <= 1) return messages;

  const firstUser = messages[0];
  const middle = messages.slice(1, splitIdx);
  const recent = messages.slice(splitIdx);

  const summaryLines = middle.map((m, i) => {
    const text = summarizeContent(m.content);
    return `- Turn ${i + 1} (${m.role}): ${text.replace(/\s+/g, " ")}`;
  });

  const compactedBlock: Anthropic.MessageParam = {
    role: "user",
    content: `<compacted_history>\n${summaryLines.join("\n")}\n</compacted_history>`,
  };

  return [firstUser, compactedBlock, ...recent];
}

/**
 * Preserve all assistant content blocks—especially `thinking` blocks with `signature`—
 * when appending to multi-turn message history.
 */
export function appendAssistantTurn(
  messages: Anthropic.MessageParam[],
  response: Anthropic.Message,
): Anthropic.MessageParam[] {
  return [
    ...messages,
    {
      role: "assistant",
      content: response.content,
    },
  ];
}

const STATIC_POLICY = `<role>
You are OrderOps Triage Agent. Resolve customer and supplier exception tickets
using only verified tool outputs.
</role>
<rules>
1. Never invent order amounts, tracking numbers, or refund approvals.
2. Always check order status before proposing a refund.
</rules>`;

const SAMPLE_TOOLS: Anthropic.Tool[] = [
  {
    name: "get_order",
    description: "Fetch order details by order_id.",
    input_schema: {
      type: "object",
      properties: { order_id: { type: "string" } },
      required: ["order_id"],
    },
  },
];

async function main(): Promise<void> {
  const prompt = buildLayeredPrompt(SAMPLE_TICKET, SAMPLE_TOOLS, STATIC_POLICY);

  if (!process.env.ANTHROPIC_API_KEY) {
    console.log("[ch03] ANTHROPIC_API_KEY not set; running offline verification.");
    const bigLog = "ERP_EVENT ".repeat(3200); // ~32,000 chars (rough estimate ~8,000 tokens)
    const truncated = truncateToolResult(bigLog);
    console.log(`Truncated tool output: ${bigLog.length} -> ${truncated.length} chars`);

    const mockHistory: Anthropic.MessageParam[] = [
      ...prompt.messages,
      { role: "assistant", content: [{ type: "tool_use", id: "toolu_1", name: "get_order", input: { order_id: "ORD-2026-88412" } }] },
      { role: "user", content: [{ type: "tool_result", tool_use_id: "toolu_1", content: truncated }] },
      { role: "assistant", content: "Checked order status." },
      { role: "user", content: "Please check refund eligibility." },
      { role: "assistant", content: "Checking refund policy." },
    ];
    const compacted = compactHistory(mockHistory);
    console.log(`Compacted history: ${mockHistory.length} -> ${compacted.length} messages`);

    // Ledger demonstration (assumes 6,000-token prefix write + 4,000 billed thinking tokens)
    const cost = calculateCostUsd(MODEL, {
      input_tokens: 1200,
      output_tokens: 350 + THINKING_BUDGET_TOKENS,
      cache_creation_input_tokens: 6000,
      cache_read_input_tokens: 0,
    });
    console.log(`Estimated Turn-1 cost with Extended Thinking (ledger demo): $${cost.toFixed(6)}`);
    return;
  }

  const client = new Anthropic();
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: MAX_TOKENS,
    thinking: {
      type: "adaptive",
    },
    tools: prompt.tools,
    system: prompt.system,
    messages: prompt.messages,
  });

  const updatedMessages = appendAssistantTurn(prompt.messages, response);
  const compacted = compactHistory(updatedMessages);
  const cost = calculateCostUsd(MODEL, response.usage);
  console.log("stop_reason:", response.stop_reason);
  console.log("messages after compaction:", compacted.length);
  console.log("turn cost (USD):", cost.toFixed(6));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
