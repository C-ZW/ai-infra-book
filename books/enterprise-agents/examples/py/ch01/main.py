"""Minimal OrderOps Agent Loop with FSM stop_reason dispatch and budget guards."""

from __future__ import annotations

import json
import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.orderops_mock import OrderOpsMockBackend
from shared.types import calculate_cost_usd


@dataclass(frozen=True)
class AgentBudget:
    max_turns: int = 8
    max_total_input_tokens: int = 50_000
    max_cost_usd: float = 0.25
    wall_clock_timeout_s: float = 18.0  # OrderOps multi-step p95 SLO
    turn_timeout_s: float = 5.0


@dataclass
class AgentRunResult:
    status: str
    final_text: str
    turns: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    stop_reason: str


TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_order",
        "description": "Fetch order details by order_id and tenant_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "tenant_id": {"type": "string"},
            },
            "required": ["order_id", "tenant_id"],
        },
    },
    {
        "name": "check_inventory",
        "description": "Check warehouse inventory for a given SKU.",
        "input_schema": {
            "type": "object",
            "properties": {"sku": {"type": "string"}},
            "required": ["sku"],
        },
    },
    {
        "name": "issue_refund",
        "description": "Issue a refund for an order with an idempotency key.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "tenant_id": {"type": "string"},
                "amount_usd": {"type": "number"},
                "reason": {"type": "string"},
                "idempotency_key": {"type": "string"},
            },
            "required": ["order_id", "tenant_id", "amount_usd", "reason", "idempotency_key"],
        },
    },
]


def execute_tool(
    backend: OrderOpsMockBackend, ticket: dict[str, Any], block: Any
) -> dict[str, Any]:
    try:
        inp = block.input
        tenant_id = str(ticket["tenantId"])
        ticket_id = str(ticket["ticketId"])
        if block.name == "get_order":
            order_id = inp.get("order_id")
            if not isinstance(order_id, str) or not order_id:
                raise ValueError("order_id must be a non-empty string")
            # Bind tenant_id from authenticated ticket context
            out = backend.get_order(order_id, tenant_id)
        elif block.name == "check_inventory":
            sku = inp.get("sku")
            if not isinstance(sku, str) or not sku:
                raise ValueError("sku must be a non-empty string")
            out = backend.check_inventory(sku)
        elif block.name == "issue_refund":
            order_id = inp.get("order_id")
            amount_usd = inp.get("amount_usd")
            reason = inp.get("reason")
            if not isinstance(order_id, str) or not order_id:
                raise ValueError("order_id must be a non-empty string")
            if not isinstance(reason, str) or not reason:
                raise ValueError("reason must be a non-empty string")
            if (
                not isinstance(amount_usd, (int, float))
                or isinstance(amount_usd, bool)
                or not math.isfinite(amount_usd)
                or amount_usd <= 0
            ):
                raise ValueError("amount_usd must be a finite positive number")
            idempotency_key = f"refund:{tenant_id}:{ticket_id}:{order_id}"
            out = backend.issue_refund(
                order_id=order_id,
                tenant_id=tenant_id,
                amount_usd=float(amount_usd),
                reason=reason,
                idempotency_key=idempotency_key,
            )
        else:
            return {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps({"error": f"Unknown tool: {block.name}"}),
                "is_error": True,
            }
        return {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": json.dumps(out),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": json.dumps({"error": str(exc)}),
            "is_error": True,
        }


def run_orderops_agent(
    client: anthropic.Anthropic,
    ticket: dict[str, Any],
    budget: AgentBudget = AgentBudget(),
    model: str = "claude-sonnet-5-5",
) -> AgentRunResult:
    backend = OrderOpsMockBackend()
    started_at = time.monotonic()
    messages: list[dict[str, Any]] = [{"role": "user", "content": json.dumps(ticket)}]

    turns = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost_usd = 0.0

    while turns < budget.max_turns:
        elapsed = time.monotonic() - started_at
        if elapsed >= budget.wall_clock_timeout_s:
            return AgentRunResult(
                status="timeout",
                final_text=f"Aborted: wall-clock timeout ({budget.wall_clock_timeout_s}s) reached.",
                turns=turns,
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                total_cost_usd=total_cost_usd,
                stop_reason="wall_clock_timeout",
            )

        turns += 1
        turn_timeout = min(budget.turn_timeout_s, budget.wall_clock_timeout_s - elapsed)
        try:
            response = client.messages.create(
                model=model,
                max_tokens=1024,
                system=(
                    "You are OrderOps Agent. Inspect the ticket, verify order/inventory "
                    "state via tools, and resolve or escalate concisely."
                ),
                tools=TOOLS,
                messages=messages,
                timeout=turn_timeout,
            )
        except anthropic.APITimeoutError:
            post_elapsed = time.monotonic() - started_at
            is_wall_clock = post_elapsed >= budget.wall_clock_timeout_s
            return AgentRunResult(
                status="timeout",
                final_text=(
                    f"Aborted: {'wall-clock' if is_wall_clock else 'turn'} timeout reached."
                ),
                turns=turns,
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                total_cost_usd=total_cost_usd,
                stop_reason="wall_clock_timeout" if is_wall_clock else "turn_timeout",
            )
        except anthropic.APIError as exc:
            return AgentRunResult(
                status="error",
                final_text=f"Aborted: API error ({exc})",
                turns=turns,
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                total_cost_usd=total_cost_usd,
                stop_reason="api_error",
            )

        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens
        total_cost_usd += calculate_cost_usd(
            model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

        if (
            total_input_tokens > budget.max_total_input_tokens
            or total_cost_usd > budget.max_cost_usd
        ):
            return AgentRunResult(
                status="budget_exceeded",
                final_text=(
                    f"Aborted: budget exceeded (tokens={total_input_tokens}, "
                    f"cost=${total_cost_usd:.4f})."
                ),
                turns=turns,
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                total_cost_usd=total_cost_usd,
                stop_reason="budget_exceeded",
            )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            text = "\n".join(b.text for b in response.content if b.type == "text")
            return AgentRunResult(
                status="completed",
                final_text=text,
                turns=turns,
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                total_cost_usd=total_cost_usd,
                stop_reason="end_turn",
            )

        if response.stop_reason == "tool_use":
            if turns >= budget.max_turns:
                return AgentRunResult(
                    status="budget_exceeded",
                    final_text=f"Aborted: reached max_turns={budget.max_turns} before tool execution.",
                    turns=turns,
                    total_input_tokens=total_input_tokens,
                    total_output_tokens=total_output_tokens,
                    total_cost_usd=total_cost_usd,
                    stop_reason="max_turns",
                )
            if time.monotonic() - started_at >= budget.wall_clock_timeout_s:
                return AgentRunResult(
                    status="timeout",
                    final_text=(
                        f"Aborted: wall-clock timeout ({budget.wall_clock_timeout_s}s) "
                        "reached before tool dispatch."
                    ),
                    turns=turns,
                    total_input_tokens=total_input_tokens,
                    total_output_tokens=total_output_tokens,
                    total_cost_usd=total_cost_usd,
                    stop_reason="wall_clock_timeout",
                )
            tool_results = [
                execute_tool(backend, ticket, b)
                for b in response.content
                if b.type == "tool_use"
            ]
            messages.append({"role": "user", "content": tool_results})
            continue

        if response.stop_reason == "refusal":
            return AgentRunResult(
                status="refused",
                final_text="Model refused to process the request.",
                turns=turns,
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                total_cost_usd=total_cost_usd,
                stop_reason="refusal",
            )

        return AgentRunResult(
            status="error",
            final_text=f"Aborted: stop_reason={response.stop_reason}",
            turns=turns,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_cost_usd=total_cost_usd,
            stop_reason=str(response.stop_reason),
        )

    return AgentRunResult(
        status="budget_exceeded",
        final_text=f"Aborted: reached max_turns={budget.max_turns}.",
        turns=turns,
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        total_cost_usd=total_cost_usd,
        stop_reason="max_turns",
    )


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set; skipping live API call.")
        return

    client = anthropic.Anthropic()
    sample_ticket = {
        "ticketId": "TKT-2026-10492",
        "tenantId": "tenant-apac-01",
        "customerId": "CUST-9012",
        "orderId": "ORD-2026-88412",
        "category": "shipping_delay",
        "priority": "high",
        "subject": "Order delayed past promised date",
        "body": "Please check order ORD-2026-88412 status and inventory for SKU-IND-401.",
        "createdAt": "2026-11-21T10:00:00Z",
    }
    result = run_orderops_agent(client, sample_ticket)
    print(json.dumps(result.__dict__, indent=2))


if __name__ == "__main__":
    main()
