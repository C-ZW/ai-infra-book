"""ch02 runnable example: Strict Tool Use, Pydantic output_config, Idempotent Refund, and Stateless Streamable HTTP MCP Server.

Note: In-memory stores in this file are single-process demonstrations only;
production deployments must back idempotency and order state with PostgreSQL + Redis.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import threading
import uuid
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Literal

from anthropic import Anthropic
from pydantic import BaseModel, Field

# Ensure shared/ is importable when running directly
EXAMPLES_PY_DIR = Path(__file__).resolve().parent.parent
if str(EXAMPLES_PY_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_PY_DIR))

from shared.types import calculate_cost_usd  # noqa: E402

READ_ONLY_TOOL_NAMES = (
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
)

MUTATING_TOOL_NAMES = (
    "issue_refund",
    "create_replacement_order",
    "update_shipping_address",
    "cancel_order",
    "apply_store_credit",
    "escalate_to_hitl",
)

REASON_CODES = (
    "shipping_delay",
    "damaged_item",
    "inventory_shortage",
    "invoice_error",
)

ORDEROPS_TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_order",
        "description": "Fetch order details, line items, and promised delivery date.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string"},
                "order_id": {"type": "string"},
            },
            "required": ["tenant_id", "order_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "issue_refund",
        "description": (
            "Issue a customer refund. Run with dry_run=true first, then execute "
            "with dry_run=false and a deterministic idempotency_key."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string"},
                "order_id": {"type": "string"},
                "amount_usd": {"type": "number"},
                "reason_code": {
                    "type": "string",
                    "enum": list(REASON_CODES),
                },
                "idempotency_key": {"type": "string"},
                "dry_run": {"type": "boolean"},
            },
            "required": [
                "tenant_id",
                "order_id",
                "amount_usd",
                "reason_code",
                "idempotency_key",
                "dry_run",
            ],
            "additionalProperties": False,
        },
    },
]


class TicketResolution(BaseModel):
    ticket_id: str
    decision: Literal["auto_resolved", "refund_issued", "escalated_hitl"]
    refund_id: str | None
    amount_usd: float = Field(ge=0)
    confidence_score: float = Field(ge=0, le=1)
    summary: str


def _parse_cents(amount_usd: Any) -> int | None:
    if isinstance(amount_usd, bool) or not isinstance(amount_usd, (int, float)):
        return None
    if not math.isfinite(amount_usd) or amount_usd <= 0:
        return None
    try:
        dec = Decimal(str(amount_usd))
    except InvalidOperation:
        return None
    if dec.as_tuple().exponent < -2:
        return None
    cents = int((dec * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return cents if cents > 0 else None


class IdempotentRefundExecutor:
    """Thread-safe in-memory idempotent refund executor (single-process demo)."""

    def __init__(self, auto_approve_limit_usd: float = 100.0) -> None:
        self._lock = threading.Lock()
        self._store: dict[tuple[str, str], tuple[str, dict[str, Any]]] = {}
        self._auto_approve_limit_cents = int(round(auto_approve_limit_usd * 100))

    def execute(
        self,
        tenant_id: Any,
        order_id: Any,
        amount_usd: Any,
        reason_code: Any,
        idempotency_key: Any,
        dry_run: Any,
    ) -> tuple[str, bool]:
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            return json.dumps({"error_code": "INVALID_TENANT", "message": "tenant_id must be a non-empty string."}), True
        if not isinstance(order_id, str) or not order_id.strip():
            return json.dumps({"error_code": "INVALID_ORDER", "message": "order_id must be a non-empty string."}), True
        if reason_code not in REASON_CODES:
            return json.dumps({"error_code": "INVALID_REASON", "message": f"reason_code must be one of {REASON_CODES}."}), True
        if not isinstance(idempotency_key, str) or not idempotency_key.strip():
            return json.dumps({"error_code": "INVALID_IDEMPOTENCY_KEY", "message": "idempotency_key must be a non-empty string."}), True
        if not isinstance(dry_run, bool):
            return json.dumps({"error_code": "INVALID_DRY_RUN", "message": "dry_run must be a boolean."}), True

        cents = _parse_cents(amount_usd)
        if cents is None:
            return (
                json.dumps(
                    {
                        "error_code": "INVALID_AMOUNT",
                        "message": "amount_usd must be a finite number > 0 with at most 2 decimal places.",
                    }
                ),
                True,
            )

        normalized_amount = cents / 100.0
        payload_hash = hashlib.sha256(
            json.dumps(
                {
                    "tenant_id": tenant_id,
                    "order_id": order_id,
                    "amount_cents": cents,
                    "reason_code": reason_code,
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        store_key = (tenant_id, idempotency_key)

        with self._lock:
            existing = self._store.get(store_key)
            if existing is not None:
                existing_hash, committed = existing
                if existing_hash != payload_hash:
                    return (
                        json.dumps(
                            {
                                "error_code": "IDEMPOTENCY_PAYLOAD_MISMATCH",
                                "message": "idempotency_key already used with different parameters.",
                            }
                        ),
                        True,
                    )
                cached = dict(committed)
                cached["deduplicated"] = True
                return json.dumps(cached), False

            if cents > self._auto_approve_limit_cents:
                return (
                    json.dumps(
                        {
                            "dry_run": dry_run,
                            "would_approve": False,
                            "order_id": order_id,
                            "amount_usd": normalized_amount,
                            "idempotency_key": idempotency_key,
                            "status": "pending_hitl",
                            "reason": f"Amount ${normalized_amount:.2f} exceeds auto-approve cap ${self._auto_approve_limit_cents / 100:.2f}",
                        }
                    ),
                    False,
                )

            if dry_run:
                return (
                    json.dumps(
                        {
                            "dry_run": True,
                            "would_approve": True,
                            "order_id": order_id,
                            "amount_usd": normalized_amount,
                            "idempotency_key": idempotency_key,
                        }
                    ),
                    False,
                )

            committed = {
                "refund_id": f"REF-{uuid.uuid4().hex[:12].upper()}",
                "tenant_id": tenant_id,
                "order_id": order_id,
                "amount_usd": normalized_amount,
                "reason_code": reason_code,
                "idempotency_key": idempotency_key,
                "status": "approved",
            }
            self._store[store_key] = (payload_hash, committed)
            return json.dumps(committed), False


def execute_get_order(tenant_id: Any, order_id: Any) -> tuple[str, bool]:
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        return json.dumps({"error_code": "INVALID_TENANT", "message": "tenant_id is required."}), True
    if not isinstance(order_id, str) or not order_id.strip():
        return json.dumps({"error_code": "INVALID_ORDER", "message": "order_id is required."}), True
    return (
        json.dumps(
            {
                "tenant_id": tenant_id,
                "order_id": order_id,
                "status": "delayed_in_transit",
                "total_usd": 45.0,
                "promised_delivery_date": "2026-11-18",
            }
        ),
        False,
    )


def dispatch_tool(name: str, args: dict[str, Any], executor: IdempotentRefundExecutor) -> tuple[str, bool]:
    if name == "get_order":
        return execute_get_order(args.get("tenant_id"), args.get("order_id"))
    if name == "issue_refund":
        return executor.execute(
            tenant_id=args.get("tenant_id"),
            order_id=args.get("order_id"),
            amount_usd=args.get("amount_usd"),
            reason_code=args.get("reason_code"),
            idempotency_key=args.get("idempotency_key"),
            dry_run=args.get("dry_run"),
        )
    return json.dumps({"error_code": "UNKNOWN_TOOL", "message": f"Tool not allowed: {name}"}), True


def make_mcp_handler(executor: IdempotentRefundExecutor) -> type[BaseHTTPRequestHandler]:
    allowed_origins = {"http://127.0.0.1:8787", "http://localhost:8787"}

    class StatelessMcpHandler(BaseHTTPRequestHandler):
        def _check_origin(self) -> bool:
            origin = self.headers.get("Origin")
            if origin and origin not in allowed_origins:
                self.send_response(403)
                self.end_headers()
                return False
            return True

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/mcp":
                self.send_response(405)
                self.send_header("Allow", "POST")
                self.end_headers()
                return
            self.send_response(404)
            self.end_headers()

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/mcp":
                self.send_response(404)
                self.end_headers()
                return
            if not self._check_origin():
                return

            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_response(400)
                self.end_headers()
                return
            if length <= 0 or length > 1_048_576:
                self.send_response(413 if length > 1_048_576 else 400)
                self.end_headers()
                return

            raw = self.rfile.read(length)
            try:
                rpc = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                self._send_json(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}})
                return

            if not isinstance(rpc, dict) or rpc.get("jsonrpc") != "2.0" or not isinstance(rpc.get("method"), str):
                self._send_json(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}})
                return

            rpc_id = rpc.get("id")
            method = rpc["method"]
            params = rpc.get("params") if isinstance(rpc.get("params"), dict) else {}

            if method == "notifications/initialized":
                self.send_response(202)
                self.end_headers()
                return

            if method == "initialize":
                payload = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "protocolVersion": "2025-03-26",
                        "serverInfo": {"name": "orderops-mcp-py", "version": "1.0.0"},
                        "capabilities": {"tools": {}},
                    },
                }
            elif method == "tools/list":
                payload = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "tools": [
                            {
                                "name": t["name"],
                                "description": t["description"],
                                "inputSchema": t["input_schema"],
                            }
                            for t in ORDEROPS_TOOLS
                        ]
                    },
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments")
                if not isinstance(tool_name, str) or not isinstance(args, dict):
                    payload = {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "error": {"code": -32602, "message": "Invalid params: name (str) and arguments (object) required."},
                    }
                elif tool_name not in {"get_order", "issue_refund"}:
                    payload = {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
                    }
                else:
                    content, is_error = dispatch_tool(tool_name, args, executor)
                    payload = {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "result": {
                            "content": [{"type": "text", "text": content}],
                            "isError": is_error,
                        },
                    }
            else:
                payload = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }

            self._send_json(200, payload)

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return StatelessMcpHandler


def run_agent_loop(client: Anthropic, executor: IdempotentRefundExecutor) -> TicketResolution | None:
    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": (
                "Ticket TKT-101 for tenant TENANT-ACME: order ORD-9042 is delayed. "
                "Check the order, run issue_refund dry_run=true for $45 (shipping_delay), "
                "then commit if approved, and return the structured TicketResolution."
            ),
        }
    ]
    max_turns = 8
    for _ in range(max_turns):
        resp = client.messages.parse(
            model="claude-sonnet-5-5",
            max_tokens=1024,
            tools=ORDEROPS_TOOLS,
            output_format=TicketResolution,
            messages=messages,
        )
        cost = calculate_cost_usd(
            "claude-sonnet-5-5",
            resp.usage.input_tokens,
            resp.usage.output_tokens,
        )
        print(f"stop_reason={resp.stop_reason}, cost=${cost:.6f}")

        if resp.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": resp.content})
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    content, is_error = dispatch_tool(block.name, dict(block.input), executor)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": content,
                            "is_error": is_error,
                        }
                    )
            messages.append({"role": "user", "content": tool_results})
            continue

        if resp.stop_reason == "end_turn":
            return resp.parsed_output

        print(f"Loop terminated with stop_reason={resp.stop_reason}")
        return None
    return None


def run_demo() -> None:
    executor = IdempotentRefundExecutor()
    key = "refund:TENANT-ACME:ORD-9042:TKT-101"
    print("Dry-run:", executor.execute("TENANT-ACME", "ORD-9042", 45.0, "shipping_delay", key, True))
    print("Commit:", executor.execute("TENANT-ACME", "ORD-9042", 45.0, "shipping_delay", key, False))
    print("Replay:", executor.execute("TENANT-ACME", "ORD-9042", 45.0, "shipping_delay", key, False))

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set; skipping live Claude API call.")
        return

    client = Anthropic()
    resolution = run_agent_loop(client, executor)
    if resolution is not None:
        print("Structured resolution:", resolution.model_dump_json())


if __name__ == "__main__":
    if "--serve" in sys.argv:
        server = ThreadingHTTPServer(("127.0.0.1", 8787), make_mcp_handler(IdempotentRefundExecutor()))
        print("Stateless Streamable HTTP MCP Server listening on http://127.0.0.1:8787/mcp")
        server.serve_forever()
    else:
        run_demo()
