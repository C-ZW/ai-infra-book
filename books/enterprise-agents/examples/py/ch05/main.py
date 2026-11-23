"""ch05: Multi-Agent Orchestration — Router, Orchestrator-Workers & Handoff Contract.

Demonstrates:
1. Haiku Router (0 tools) classifying OrderOps tickets into specialist lanes.
2. Orchestrator-Workers fan-out with asyncio.gather(..., return_exceptions=True) & timeouts.
3. Compressed WorkerHandoff contract (no raw tool logs leaked to parent context).
4. Opus Refund Specialist escalation for high-risk mutating operations.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

# Ensure examples/py is on sys.path when executed directly
PY_ROOT = Path(__file__).resolve().parents[1]
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from shared.orderops_mock import OrderOpsMockBackend  # noqa: E402
from shared.types import calculate_cost_usd  # noqa: E402

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic

backend = OrderOpsMockBackend()
SAMPLE_TICKETS: list[dict[str, Any]] = [
    {
        "ticket_id": "TKT-5001",
        "tenant_id": "tenant-apac-01",
        "customer_id": "CUST-9012",
        "order_id": "ORD-2026-88412",
        "category": "shipping_delay",
        "priority": "high",
        "subject": "Shipment delayed past promised date",
        "body": "Order ORD-2026-88412 was promised 2026-11-18. Please check carrier and warehouse.",
    },
    {
        "ticket_id": "TKT-5002",
        "tenant_id": "tenant-eu-02",
        "customer_id": "CUST-3318",
        "order_id": "ORD-2026-88901",
        "category": "refund_request",
        "priority": "critical",
        "subject": "Requesting full refund ($1,850)",
        "body": "Customer requests full refund for ORD-2026-88901.",
    },
]

SpecialistLane = Literal[
    "shipping_investigator",
    "inventory_investigator",
    "refund_arbitrator",
]
ReadOnlyTask = Literal["carrier_status", "warehouse_stock", "billing_ledger"]

WORKER_TIMEOUT_SEC = 8.0
WORKER_MAX_TURNS = 4


@dataclass(frozen=True)
class RouteDecision:
    lane: SpecialistLane
    parallel_read_only_tasks: list[ReadOnlyTask]
    confidence: float
    reason: str


@dataclass(frozen=True)
class WorkerHandoff:
    worker_id: str
    task: str
    status: Literal["ok", "timeout", "error"]
    summary: str
    facts: dict[str, Any]
    latency_ms: int
    cost_usd: float


@dataclass(frozen=True)
class OrchestrationResult:
    ticket_id: str
    route: RouteDecision
    handoffs: list[WorkerHandoff]
    final_action: str
    total_cost_usd: float
    total_latency_ms: int


async def route_ticket(
    client: AsyncAnthropic | None,
    ticket: dict[str, Any],
) -> tuple[RouteDecision, float]:
    """Haiku Router: 0 tools, minimal prefix, structured JSON routing decision."""
    if client is None:
        decision = (
            RouteDecision(
                lane="refund_arbitrator",
                parallel_read_only_tasks=["carrier_status", "billing_ledger"],
                confidence=0.96,
                reason="Refund request requires carrier delivery check and ledger verification.",
            )
            if ticket["category"] == "refund_request"
            else RouteDecision(
                lane="shipping_investigator",
                parallel_read_only_tasks=["carrier_status", "warehouse_stock"],
                confidence=0.94,
                reason="Shipping delay requires carrier tracking and warehouse dispatch check.",
            )
        )
        cost = calculate_cost_usd("claude-haiku-5-5", input_tokens=450, output_tokens=90)
        return decision, cost

    response = await client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=256,
        system=(
            "You are the OrderOps ticket router. Output ONLY valid JSON matching "
            '{"lane": "shipping_investigator"|"inventory_investigator"|"refund_arbitrator", '
            '"parallel_read_only_tasks": list[str], "confidence": float, "reason": str}.'
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"Ticket {ticket['ticket_id']} [{ticket['category']}/{ticket['priority']}]: "
                    f"{ticket['subject']}\n{ticket['body']}"
                ),
            }
        ],
    )
    raw = next((b.text for b in response.content if b.type == "text"), "{}")
    parsed = json.loads(raw)
    decision = RouteDecision(
        lane=parsed["lane"],
        parallel_read_only_tasks=parsed["parallel_read_only_tasks"],
        confidence=float(parsed["confidence"]),
        reason=str(parsed["reason"]),
    )
    cost = calculate_cost_usd(
        "claude-haiku-5-5",
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
    return decision, cost


async def run_read_only_worker(
    ticket: dict[str, Any],
    task: ReadOnlyTask,
) -> WorkerHandoff:
    """Read-only investigation worker with isolated context and compressed handoff."""
    start = time.monotonic()
    order = backend.get_order(ticket["order_id"], ticket["tenant_id"])
    order_not_found = "error" in order
    facts: dict[str, Any] = (
        {"order_id": ticket["order_id"], "status": "not_found"}
        if order_not_found
        else {
            "order_id": order["order_id"],
            "status": order["status"],
            "total_usd": order["total_usd"],
            "carrier_tracking": order.get("carrier_tracking", "N/A"),
        }
    )
    cost = calculate_cost_usd("claude-haiku-5-5", input_tokens=1_200, output_tokens=180)
    elapsed_ms = int((time.monotonic() - start) * 1000)
    return WorkerHandoff(
        worker_id=f"worker-{task}",
        task=task,
        status="error" if order_not_found else "ok",
        summary=f"[{task}] Order {ticket['order_id']} status={facts['status']}, max_turns={WORKER_MAX_TURNS}",
        facts=facts,
        latency_ms=elapsed_ms,
        cost_usd=cost,
    )


async def orchestrate_ticket(
    client: AsyncAnthropic | None,
    ticket: dict[str, Any],
) -> OrchestrationResult:
    """Fan out read-only workers in parallel, collect compressed handoffs, escalate if needed."""
    t0 = time.monotonic()
    decision, router_cost = await route_ticket(client, ticket)

    coros = [
        asyncio.wait_for(run_read_only_worker(ticket, task), timeout=WORKER_TIMEOUT_SEC)
        for task in decision.parallel_read_only_tasks
    ]
    results = await asyncio.gather(*coros, return_exceptions=True)

    handoffs: list[WorkerHandoff] = []
    for task, res in zip(decision.parallel_read_only_tasks, results):
        if isinstance(res, WorkerHandoff):
            handoffs.append(res)
        elif isinstance(res, TimeoutError):
            handoffs.append(
                WorkerHandoff(
                    worker_id=f"worker-{task}",
                    task=task,
                    status="timeout",
                    summary=f"Worker timed out after {WORKER_TIMEOUT_SEC}s",
                    facts={},
                    latency_ms=int(WORKER_TIMEOUT_SEC * 1000),
                    cost_usd=0.0,
                )
            )
        else:
            handoffs.append(
                WorkerHandoff(
                    worker_id=f"worker-{task}",
                    task=task,
                    status="error",
                    summary=f"Worker error: {res}",
                    facts={},
                    latency_ms=0,
                    cost_usd=0.0,
                )
            )

    worker_cost = sum(h.cost_usd for h in handoffs)
    specialist_cost = 0.0
    final_action = "resolved_read_only"

    if decision.lane == "refund_arbitrator":
        specialist_cost = calculate_cost_usd(
            "claude-opus-5-5",
            input_tokens=2_800,
            output_tokens=320,
        )
        required_tasks = ("carrier_status", "billing_ledger")
        handoff_map = {h.task: h for h in handoffs}
        missing_or_failed = [
            req
            for req in required_tasks
            if req not in handoff_map
            or handoff_map[req].status != "ok"
            or handoff_map[req].facts.get("order_id") != ticket["order_id"]
        ]
        final_action = (
            f"degraded_pending_hitl(missing_or_failed={','.join(missing_or_failed)})"
            if missing_or_failed
            else "refund_approved_by_opus_specialist"
        )
    else:
        failed = [h.task for h in handoffs if h.status != "ok"]
        if failed or not handoffs:
            final_action = f"degraded_pending_hitl(failed={','.join(failed) or 'none'})"

    return OrchestrationResult(
        ticket_id=ticket["ticket_id"],
        route=decision,
        handoffs=handoffs,
        final_action=final_action,
        total_cost_usd=router_cost + worker_cost + specialist_cost,
        total_latency_ms=int((time.monotonic() - t0) * 1000),
    )


async def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = None
    if api_key:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=api_key)
    mode = "LIVE API" if client else "OFFLINE SIMULATION"
    print(f"[ch05] Running OrderOps Orchestrator ({mode})")

    for ticket in SAMPLE_TICKETS[:2]:
        result = await orchestrate_ticket(client, ticket)
        print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
