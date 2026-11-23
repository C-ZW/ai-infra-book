import crypto from "node:crypto";
import http from "node:http";
import { pathToFileURL } from "node:url";
import Anthropic from "@anthropic-ai/sdk";
import { zodOutputFormat } from "@anthropic-ai/sdk/helpers/zod";
import { z } from "zod";
import type { RefundResult } from "../shared/types.js";

// ============================================================================
// 1. OrderOps 18-Tool Registry (12 Read-only + 6 Mutating) with strict: true
// ============================================================================

export const READ_ONLY_TOOL_NAMES = [
  "get_ticket",
  "get_order",
  "list_customer_orders",
  "get_shipment_tracking",
  "get_inventory_level",
  "get_warehouse_sla",
  "get_refund_policy",
  "get_invoice",
  "list_payment_transactions",
  "get_carrier_status",
  "search_kb_articles",
  "get_audit_log",
] as const;

export const MUTATING_TOOL_NAMES = [
  "issue_refund",
  "create_replacement_order",
  "update_shipping_address",
  "cancel_order",
  "apply_store_credit",
  "escalate_to_hitl",
] as const;

const REASON_CODES = [
  "shipping_delay",
  "damaged_item",
  "inventory_shortage",
  "invoice_error",
] as const;

export const ORDEROPS_TOOLS: Anthropic.Tool[] = [
  {
    name: "get_order",
    description:
      "Fetch order details, line items, and promised delivery date by orderId.",
    strict: true,
    input_schema: {
      type: "object",
      properties: {
        tenant_id: { type: "string", description: "Tenant identifier" },
        order_id: { type: "string", description: "Order identifier (e.g. ORD-9042)" },
      },
      required: ["tenant_id", "order_id"],
      additionalProperties: false,
    },
  },
  {
    name: "issue_refund",
    description:
      "Issue a customer refund. Always run with dry_run=true first to validate policy caps, then execute with dry_run=false and a deterministic idempotency_key.",
    strict: true,
    input_schema: {
      type: "object",
      properties: {
        tenant_id: { type: "string" },
        order_id: { type: "string" },
        amount_usd: { type: "number", description: "Refund amount in USD (> 0)" },
        reason_code: {
          type: "string",
          enum: [...REASON_CODES],
        },
        idempotency_key: {
          type: "string",
          description: "Deterministic key: refund:<tenant_id>:<order_id>:<ticket_id>",
        },
        dry_run: {
          type: "boolean",
          description: "When true, validates limits without mutating ledger.",
        },
      },
      required: [
        "tenant_id",
        "order_id",
        "amount_usd",
        "reason_code",
        "idempotency_key",
        "dry_run",
      ],
      additionalProperties: false,
    },
  },
];

// ============================================================================
// 2. Structured Output Contract via Zod (output_config.format)
// ============================================================================

export const TicketResolutionSchema = z.object({
  ticket_id: z.string(),
  decision: z.enum(["auto_resolved", "refund_issued", "escalated_hitl"]),
  refund_id: z.string().nullable(),
  amount_usd: z.number().nonnegative(),
  confidence_score: z.number().min(0).max(1),
  summary: z.string(),
});

export type TicketResolution = z.infer<typeof TicketResolutionSchema>;

// ============================================================================
// 3. Idempotent Mutating Tool Executor (Single-Process Demo)
// ============================================================================

export interface ToolExecutionOutput {
  content: string;
  is_error: boolean;
}

function parseCents(amountUsd: unknown): number | null {
  if (typeof amountUsd !== "number" || !Number.isFinite(amountUsd) || amountUsd <= 0) {
    return null;
  }
  const scaled = amountUsd * 100;
  const rounded = Math.round(scaled);
  if (Math.abs(scaled - rounded) > 1e-6 || rounded <= 0) {
    return null;
  }
  return rounded;
}

export class IdempotentRefundExecutor {
  private readonly store = new Map<string, { payloadHash: string; result: RefundResult }>();
  private readonly autoApproveLimitCents = 10_000;

  execute(args: {
    tenant_id?: unknown;
    order_id?: unknown;
    amount_usd?: unknown;
    reason_code?: unknown;
    idempotency_key?: unknown;
    dry_run?: unknown;
  }): ToolExecutionOutput {
    if (typeof args.tenant_id !== "string" || !args.tenant_id.trim()) {
      return {
        is_error: true,
        content: JSON.stringify({ error_code: "INVALID_TENANT", message: "tenant_id must be a non-empty string." }),
      };
    }
    if (typeof args.order_id !== "string" || !args.order_id.trim()) {
      return {
        is_error: true,
        content: JSON.stringify({ error_code: "INVALID_ORDER", message: "order_id must be a non-empty string." }),
      };
    }
    if (typeof args.reason_code !== "string" || !REASON_CODES.includes(args.reason_code as (typeof REASON_CODES)[number])) {
      return {
        is_error: true,
        content: JSON.stringify({ error_code: "INVALID_REASON", message: `reason_code must be one of ${REASON_CODES.join(", ")}.` }),
      };
    }
    if (typeof args.idempotency_key !== "string" || !args.idempotency_key.trim()) {
      return {
        is_error: true,
        content: JSON.stringify({ error_code: "INVALID_IDEMPOTENCY_KEY", message: "idempotency_key must be a non-empty string." }),
      };
    }
    if (typeof args.dry_run !== "boolean") {
      return {
        is_error: true,
        content: JSON.stringify({ error_code: "INVALID_DRY_RUN", message: "dry_run must be a boolean." }),
      };
    }

    const cents = parseCents(args.amount_usd);
    if (cents === null) {
      return {
        is_error: true,
        content: JSON.stringify({
          error_code: "INVALID_AMOUNT",
          message: "amount_usd must be a finite number > 0 with at most 2 decimal places.",
        }),
      };
    }

    const normalizedAmount = cents / 100;
    const payloadHash = crypto
      .createHash("sha256")
      .update(
        JSON.stringify({
          tenant_id: args.tenant_id,
          order_id: args.order_id,
          amount_cents: cents,
          reason_code: args.reason_code,
        }),
      )
      .digest("hex");
    const storeKey = `${args.tenant_id}::${args.idempotency_key}`;

    const existing = this.store.get(storeKey);
    if (existing) {
      if (existing.payloadHash !== payloadHash) {
        return {
          is_error: true,
          content: JSON.stringify({
            error_code: "IDEMPOTENCY_PAYLOAD_MISMATCH",
            message: "idempotency_key already used with different parameters.",
          }),
        };
      }
      return {
        is_error: false,
        content: JSON.stringify({ ...existing.result, deduplicated: true }),
      };
    }

    if (cents > this.autoApproveLimitCents) {
      return {
        is_error: false,
        content: JSON.stringify({
          dry_run: args.dry_run,
          would_approve: false,
          order_id: args.order_id,
          amount_usd: normalizedAmount,
          idempotency_key: args.idempotency_key,
          status: "pending_hitl",
          reason: `Amount $${normalizedAmount.toFixed(2)} exceeds auto-approve cap $${(this.autoApproveLimitCents / 100).toFixed(2)}`,
        }),
      };
    }

    if (args.dry_run) {
      return {
        is_error: false,
        content: JSON.stringify({
          dry_run: true,
          would_approve: true,
          order_id: args.order_id,
          amount_usd: normalizedAmount,
          idempotency_key: args.idempotency_key,
        }),
      };
    }

    const committed: RefundResult = {
      refundId: `REF-${crypto.randomUUID().slice(0, 12).toUpperCase()}`,
      orderId: args.order_id,
      amountUsd: normalizedAmount,
      idempotencyKey: args.idempotency_key,
      status: "approved",
    };
    this.store.set(storeKey, { payloadHash, result: committed });
    return { is_error: false, content: JSON.stringify(committed) };
  }
}

export function executeGetOrder(args: { tenant_id?: unknown; order_id?: unknown }): ToolExecutionOutput {
  if (typeof args.tenant_id !== "string" || !args.tenant_id.trim()) {
    return { is_error: true, content: JSON.stringify({ error_code: "INVALID_TENANT", message: "tenant_id is required." }) };
  }
  if (typeof args.order_id !== "string" || !args.order_id.trim()) {
    return { is_error: true, content: JSON.stringify({ error_code: "INVALID_ORDER", message: "order_id is required." }) };
  }
  return {
    is_error: false,
    content: JSON.stringify({
      tenant_id: args.tenant_id,
      order_id: args.order_id,
      status: "delayed_in_transit",
      total_usd: 45.0,
      promised_delivery_date: "2026-11-18",
    }),
  };
}

export function dispatchTool(
  name: string,
  args: Record<string, unknown>,
  executor: IdempotentRefundExecutor,
): ToolExecutionOutput {
  if (name === "get_order") {
    return executeGetOrder(args);
  }
  if (name === "issue_refund") {
    return executor.execute(args);
  }
  return {
    is_error: true,
    content: JSON.stringify({ error_code: "UNKNOWN_TOOL", message: `Tool not allowed: ${name}` }),
  };
}

// ============================================================================
// 4. Stateless Streamable HTTP MCP Server (JSON-RPC 2.0 over POST /mcp)
// ============================================================================

const ALLOWED_ORIGINS = new Set(["http://127.0.0.1:8787", "http://localhost:8787"]);
const MAX_BODY_BYTES = 1_048_576;

export function createStatelessMcpServer(executor: IdempotentRefundExecutor): http.Server {
  return http.createServer(async (req, res) => {
    if (req.url !== "/mcp") {
      res.writeHead(404, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "Not Found" }));
      return;
    }

    if (req.method === "GET") {
      res.writeHead(405, { Allow: "POST" });
      res.end();
      return;
    }

    if (req.method !== "POST") {
      res.writeHead(405, { Allow: "POST" });
      res.end();
      return;
    }

    const origin = req.headers.origin;
    if (origin && !ALLOWED_ORIGINS.has(origin)) {
      res.writeHead(403, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "Forbidden origin" }));
      return;
    }

    const chunks: Buffer[] = [];
    let totalBytes = 0;
    for await (const chunk of req) {
      const buf = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
      totalBytes += buf.length;
      if (totalBytes > MAX_BODY_BYTES) {
        res.writeHead(413, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "Payload Too Large" }));
        return;
      }
      chunks.push(buf);
    }

    let rpc: unknown;
    try {
      rpc = JSON.parse(Buffer.concat(chunks).toString("utf8"));
    } catch (err) {
      res.writeHead(400, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          jsonrpc: "2.0",
          id: null,
          error: { code: -32700, message: err instanceof Error ? err.message : "Parse error" },
        }),
      );
      return;
    }

    if (
      typeof rpc !== "object" ||
      rpc === null ||
      (rpc as Record<string, unknown>).jsonrpc !== "2.0" ||
      typeof (rpc as Record<string, unknown>).method !== "string"
    ) {
      res.writeHead(400, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          jsonrpc: "2.0",
          id: null,
          error: { code: -32600, message: "Invalid Request" },
        }),
      );
      return;
    }

    const reqObj = rpc as {
      jsonrpc: "2.0";
      id?: string | number | null;
      method: string;
      params?: Record<string, unknown>;
    };
    const rpcId = reqObj.id ?? null;

    if (reqObj.method === "notifications/initialized") {
      res.writeHead(202);
      res.end();
      return;
    }

    if (reqObj.method === "initialize") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          jsonrpc: "2.0",
          id: rpcId,
          result: {
            protocolVersion: "2025-03-26",
            serverInfo: { name: "orderops-mcp", version: "1.0.0" },
            capabilities: { tools: {} },
          },
        }),
      );
      return;
    }

    if (reqObj.method === "tools/list") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          jsonrpc: "2.0",
          id: rpcId,
          result: {
            tools: ORDEROPS_TOOLS.map((t) => ({
              name: t.name,
              description: t.description,
              inputSchema: t.input_schema,
            })),
          },
        }),
      );
      return;
    }

    if (reqObj.method === "tools/call") {
      const toolName = reqObj.params?.name;
      const args = reqObj.params?.arguments;
      if (typeof toolName !== "string" || typeof args !== "object" || args === null || Array.isArray(args)) {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(
          JSON.stringify({
            jsonrpc: "2.0",
            id: rpcId,
            error: { code: -32602, message: "Invalid params: name (string) and arguments (object) required." },
          }),
        );
        return;
      }
      if (toolName !== "get_order" && toolName !== "issue_refund") {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(
          JSON.stringify({
            jsonrpc: "2.0",
            id: rpcId,
            error: { code: -32601, message: `Tool not found: ${toolName}` },
          }),
        );
        return;
      }
      const out = dispatchTool(toolName, args as Record<string, unknown>, executor);
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          jsonrpc: "2.0",
          id: rpcId,
          result: {
            content: [{ type: "text", text: out.content }],
            isError: out.is_error,
          },
        }),
      );
      return;
    }

    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        jsonrpc: "2.0",
        id: rpcId,
        error: { code: -32601, message: `Method not found: ${reqObj.method}` },
      }),
    );
  });
}

// ============================================================================
// 5. Claude API Agent Loop with strict: true + output_config.format
// ============================================================================

export async function runAgentLoop(
  client: Anthropic,
  executor: IdempotentRefundExecutor,
): Promise<TicketResolution | null> {
  const messages: Anthropic.MessageParam[] = [
    {
      role: "user",
      content:
        "Ticket TKT-101 for tenant TENANT-ACME: order ORD-9042 is delayed. Check the order, run issue_refund dry_run=true for $45 (shipping_delay), then commit if approved, and return the structured TicketResolution.",
    },
  ];
  const maxTurns = 8;

  for (let turn = 0; turn < maxTurns; turn += 1) {
    const response = await client.messages.parse({
      model: "claude-sonnet-5-5",
      max_tokens: 1024,
      tools: ORDEROPS_TOOLS,
      output_config: { format: zodOutputFormat(TicketResolutionSchema) },
      messages,
    });
    console.log("Stop reason:", response.stop_reason);

    if (response.stop_reason === "tool_use") {
      messages.push({ role: "assistant", content: response.content });
      const toolResults: Anthropic.ToolResultBlockParam[] = [];
      for (const block of response.content) {
        if (block.type === "tool_use") {
          const out = dispatchTool(
            block.name,
            (block.input ?? {}) as Record<string, unknown>,
            executor,
          );
          toolResults.push({
            type: "tool_result",
            tool_use_id: block.id,
            content: out.content,
            is_error: out.is_error,
          });
        }
      }
      messages.push({ role: "user", content: toolResults });
      continue;
    }

    if (response.stop_reason === "end_turn") {
      return response.parsed_output;
    }

    console.log(`Loop terminated with stop_reason=${response.stop_reason}`);
    return null;
  }
  return null;
}

export async function runStrictToolUseDemo(): Promise<void> {
  const executor = new IdempotentRefundExecutor();
  const dryRunOut = executor.execute({
    tenant_id: "TENANT-ACME",
    order_id: "ORD-9042",
    amount_usd: 45,
    reason_code: "shipping_delay",
    idempotency_key: "refund:TENANT-ACME:ORD-9042:TKT-101",
    dry_run: true,
  });
  const commitOut = executor.execute({
    tenant_id: "TENANT-ACME",
    order_id: "ORD-9042",
    amount_usd: 45,
    reason_code: "shipping_delay",
    idempotency_key: "refund:TENANT-ACME:ORD-9042:TKT-101",
    dry_run: false,
  });
  const replayOut = executor.execute({
    tenant_id: "TENANT-ACME",
    order_id: "ORD-9042",
    amount_usd: 45,
    reason_code: "shipping_delay",
    idempotency_key: "refund:TENANT-ACME:ORD-9042:TKT-101",
    dry_run: false,
  });

  console.log("Dry-run:", dryRunOut);
  console.log("Commit:", commitOut);
  console.log("Idempotent Replay:", replayOut);

  if (!process.env.ANTHROPIC_API_KEY) {
    console.log("ANTHROPIC_API_KEY not set; skipping live Claude API call.");
    return;
  }

  const client = new Anthropic();
  const resolution = await runAgentLoop(client, executor);
  if (resolution) {
    console.log("Structured resolution:", JSON.stringify(resolution));
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (process.argv.includes("--serve")) {
    const server = createStatelessMcpServer(new IdempotentRefundExecutor());
    server.listen(8787, "127.0.0.1", () => {
      console.log("Stateless Streamable HTTP MCP Server listening on http://127.0.0.1:8787/mcp");
    });
  } else {
    void runStrictToolUseDemo();
  }
}
