"""Shared domain types and 2026-11 Claude API pricing helpers for OrderOps examples."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TicketPriority = Literal["low", "medium", "high", "critical"]
TicketCategory = Literal[
    "shipping_delay",
    "inventory_mismatch",
    "refund_request",
    "invoice_discrepancy",
    "sla_breach",
]


@dataclass(frozen=True)
class ModelPricing:
    input_per_mtok: float
    output_per_mtok: float
    cache_write_5m_mult: float = 1.25
    cache_write_1h_mult: float = 2.0
    cache_read_mult: float = 0.05


CLAUDE_PRICING_2026_11: dict[str, ModelPricing] = {
    "claude-haiku-5-5": ModelPricing(0.10, 0.50, 1.25, 2.0, 0.10),
    "claude-sonnet-5-5": ModelPricing(2.00, 10.00, 1.25, 2.0, 0.05),
    "claude-opus-5-5": ModelPricing(4.00, 20.00, 1.25, 2.0, 0.05),
}


def calculate_cost_usd(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_creation_input_tokens: int = 0,
    cache_read_input_tokens: int = 0,
    ttl: Literal["5m", "1h"] = "5m",
) -> float:
    pricing = CLAUDE_PRICING_2026_11.get(model, CLAUDE_PRICING_2026_11["claude-sonnet-5-5"])
    write_mult = pricing.cache_write_1h_mult if ttl == "1h" else pricing.cache_write_5m_mult
    return (
        (input_tokens * pricing.input_per_mtok) / 1_000_000
        + (output_tokens * pricing.output_per_mtok) / 1_000_000
        + (cache_creation_input_tokens * pricing.input_per_mtok * write_mult) / 1_000_000
        + (cache_read_input_tokens * pricing.input_per_mtok * pricing.cache_read_mult) / 1_000_000
    )
