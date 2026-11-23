"""OrderOps cost & latency optimization: Model Router, Prompt Caching, and Waterfall."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.types import TicketCategory, TicketPriority, calculate_cost_usd


@dataclass(frozen=True)
class RoutingDecision:
    model: str
    reason: str
    batch_eligible: bool


def route_ticket(category: TicketCategory, priority: TicketPriority) -> RoutingDecision:
    if priority == "critical" or category == "sla_breach":
        return RoutingDecision("claude-opus-5-5", "high_risk_escalation", False)
    if category == "invoice_discrepancy" and priority == "low":
        return RoutingDecision("claude-haiku-5-5", "offline_reconciliation", True)
    if priority == "low" or category == "shipping_delay":
        return RoutingDecision("claude-haiku-5-5", "standard_triage", False)
    return RoutingDecision("claude-sonnet-5-5", "standard_workflow", False)


def build_cached_prefix_blocks(
    system_prompt: str,
    tool_schemas: list[dict[str, object]],
    ttl: str = "5m",
) -> dict[str, object]:
    tools = [
        {**tool, "cache_control": {"type": "ephemeral", "ttl": ttl}}
        if idx == len(tool_schemas) - 1
        else tool
        for idx, tool in enumerate(tool_schemas)
    ]
    return {
        "system": [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral", "ttl": ttl},
            }
        ],
        "tools": tools,
    }


def select_tools_for_category(
    category: TicketCategory,
    all_tools: list[dict[str, str]],
) -> list[dict[str, str]]:
    allowed_groups: dict[TicketCategory, set[str]] = {
        "shipping_delay": {"read", "shipping"},
        "inventory_mismatch": {"read", "shipping"},
        "refund_request": {"read", "refund"},
        "invoice_discrepancy": {"read", "invoice"},
        "sla_breach": {"read", "refund", "shipping"},
    }
    groups = allowed_groups[category]
    return sorted(
        [t for t in all_tools if t["group"] in groups],
        key=lambda t: t["name"],
    )


def simulate_orderops_waterfall(
    ttl: str = "5m",
    inference_geo: str = "global",
) -> dict[str, float]:
    monthly_tickets = 1_500_000
    geo_multiplier = 1.1 if inference_geo == "us" else 1.0
    baseline_per_ticket = calculate_cost_usd(
        "claude-sonnet-5-5",
        input_tokens=42_000,
        output_tokens=1_750,
    )

    haiku = calculate_cost_usd(
        "claude-haiku-5-5",
        input_tokens=4_500,
        output_tokens=1_050,
        cache_creation_input_tokens=1_350,
        cache_read_input_tokens=12_150,
        ttl=ttl,
    )
    sonnet = calculate_cost_usd(
        "claude-sonnet-5-5",
        input_tokens=4_500,
        output_tokens=1_050,
        cache_creation_input_tokens=1_350,
        cache_read_input_tokens=12_150,
        ttl=ttl,
    )
    opus = calculate_cost_usd(
        "claude-opus-5-5",
        input_tokens=4_500,
        output_tokens=1_050,
        cache_creation_input_tokens=1_350,
        cache_read_input_tokens=12_150,
        ttl=ttl,
    )

    weighted = (0.60 * haiku + 0.35 * sonnet + 0.05 * opus) * 0.85 * geo_multiplier
    return {
        "baseline_monthly_usd": round(baseline_per_ticket * monthly_tickets, 2),
        "optimized_monthly_usd": round(weighted * monthly_tickets, 2),
        "optimized_per_ticket_usd": round(weighted, 6),
        "reduction_pct": round(((baseline_per_ticket - weighted) / baseline_per_ticket) * 100, 1),
    }


if __name__ == "__main__":
    print("Routing:", route_ticket("shipping_delay", "low"))
    print("Waterfall:", simulate_orderops_waterfall())
