"""Production Readiness Review (PRR) & Config Validator for OrderOps."""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared.types import CLAUDE_PRICING_2026_11  # noqa: E402

AutonomyLevel = Literal["L1", "L2", "L3"]


@dataclass(frozen=True)
class ProductionConfig:
    service_name: str
    autonomy_level: AutonomyLevel
    triage_model: str
    worker_model: str
    inference_geo: Literal["global", "us"]
    triage_p95_sec: float
    multi_step_p95_sec: float
    monthly_budget_cap_usd: float
    daily_ticket_volume: int
    estimated_base_cost_per_ticket_usd: float
    max_turns: int
    llm_timeout_ms: int
    tool_timeout_ms: int
    wall_clock_timeout_ms: int
    hitl_required_for_mutating: bool
    max_auto_refund_usd: float
    pass_at_1: float
    pass_pow_3: float
    otel_enabled: bool
    audit_retention_days: int


@dataclass(frozen=True)
class PrrCheckResult:
    gate: str
    status: Literal["PASS", "FAIL"]
    detail: str


def _is_pos(n: float) -> bool:
    return math.isfinite(n) and n > 0


def _is_unit_interval(n: float) -> bool:
    return math.isfinite(n) and 0.0 <= n <= 1.0


def validate_production_config(cfg: ProductionConfig) -> list[PrrCheckResult]:
    results: list[PrrCheckResult] = []

    models_ok = (
        cfg.triage_model in CLAUDE_PRICING_2026_11
        and cfg.worker_model in CLAUDE_PRICING_2026_11
    )
    results.append(
        PrrCheckResult(
            "model_registry",
            "PASS" if models_ok else "FAIL",
            f"triage={cfg.triage_model}, worker={cfg.worker_model}",
        )
    )

    slo_ok = (
        _is_pos(cfg.triage_p95_sec)
        and _is_pos(cfg.multi_step_p95_sec)
        and cfg.triage_p95_sec <= 2.5
        and cfg.multi_step_p95_sec <= 18.0
    )
    results.append(
        PrrCheckResult(
            "latency_slo",
            "PASS" if slo_ok else "FAIL",
            f"triageP95={cfg.triage_p95_sec}s (<=2.5s), multiStepP95={cfg.multi_step_p95_sec}s (<=18s)",
        )
    )

    geo_valid = cfg.inference_geo in ("global", "us")
    geo_mult = 1.1 if cfg.inference_geo == "us" else 1.0
    est_monthly_usd = (
        cfg.daily_ticket_volume * 30 * cfg.estimated_base_cost_per_ticket_usd * geo_mult
    )
    cost_ok = (
        geo_valid
        and _is_pos(cfg.monthly_budget_cap_usd)
        and _is_pos(cfg.daily_ticket_volume)
        and _is_pos(cfg.estimated_base_cost_per_ticket_usd)
        and est_monthly_usd <= cfg.monthly_budget_cap_usd
    )
    results.append(
        PrrCheckResult(
            "cost_cap",
            "PASS" if cost_ok else "FAIL",
            f"est=${est_monthly_usd:,.0f}/mo (geo={cfg.inference_geo} {geo_mult}x) <= cap=${cfg.monthly_budget_cap_usd:,.0f}/mo",
        )
    )

    autonomy_ok = cfg.autonomy_level in ("L1", "L2", "L3") and isinstance(
        cfg.hitl_required_for_mutating, bool
    )
    if cfg.autonomy_level == "L2" and not cfg.hitl_required_for_mutating:
        autonomy_ok = False
    if cfg.autonomy_level == "L3" and (
        not _is_pos(cfg.max_auto_refund_usd)
        or cfg.max_auto_refund_usd > 50.0
        or cfg.pass_pow_3 < 0.95
    ):
        autonomy_ok = False
    results.append(
        PrrCheckResult(
            "autonomy_guardrail",
            "PASS" if autonomy_ok else "FAIL",
            f"level={cfg.autonomy_level}, hitl_mutating={cfg.hitl_required_for_mutating}",
        )
    )

    timeout_ok = (
        _is_pos(cfg.tool_timeout_ms)
        and _is_pos(cfg.llm_timeout_ms)
        and _is_pos(cfg.wall_clock_timeout_ms)
        and cfg.tool_timeout_ms < cfg.llm_timeout_ms < cfg.wall_clock_timeout_ms
        and isinstance(cfg.max_turns, int)
        and 1 <= cfg.max_turns <= 12
    )
    results.append(
        PrrCheckResult(
            "timeout_hierarchy",
            "PASS" if timeout_ok else "FAIL",
            f"tool={cfg.tool_timeout_ms}ms < llm={cfg.llm_timeout_ms}ms < wall={cfg.wall_clock_timeout_ms}ms, maxTurns={cfg.max_turns}",
        )
    )

    eval_ok = (
        _is_unit_interval(cfg.pass_at_1)
        and _is_unit_interval(cfg.pass_pow_3)
        and cfg.pass_at_1 >= 0.92
        and cfg.pass_pow_3 >= 0.85
    )
    results.append(
        PrrCheckResult(
            "eval_baseline",
            "PASS" if eval_ok else "FAIL",
            f"Pass@1={cfg.pass_at_1}, Pass^3={cfg.pass_pow_3}",
        )
    )

    obs_ok = (
        cfg.otel_enabled is True
        and isinstance(cfg.audit_retention_days, int)
        and cfg.audit_retention_days >= 90
    )
    results.append(
        PrrCheckResult(
            "observability_audit",
            "PASS" if obs_ok else "FAIL",
            f"otel={cfg.otel_enabled}, retention={cfg.audit_retention_days}d (>=90d)",
        )
    )

    return results


def main() -> int:
    cfg = ProductionConfig(
        service_name="orderops-agent-prod",
        autonomy_level="L2",
        triage_model="claude-haiku-5-5",
        worker_model="claude-sonnet-5-5",
        inference_geo="us",
        triage_p95_sec=2.1,
        multi_step_p95_sec=15.4,
        monthly_budget_cap_usd=18_000,
        daily_ticket_volume=50_000,
        estimated_base_cost_per_ticket_usd=0.0108,
        max_turns=8,
        llm_timeout_ms=12_000,
        tool_timeout_ms=5_000,
        wall_clock_timeout_ms=60_000,
        hitl_required_for_mutating=True,
        max_auto_refund_usd=0.0,
        pass_at_1=0.94,
        pass_pow_3=0.88,
        otel_enabled=True,
        audit_retention_days=180,
    )
    checks = validate_production_config(cfg)
    failed = 0
    for c in checks:
        print(f"[{c.status}] {c.gate}: {c.detail}")
        if c.status == "FAIL":
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
