"""Runnable ch10 example: OpenTelemetry-style Agent Tracer, Cost Attribution, and Budget Circuit Breaker."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# Ensure shared package is importable when run directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.types import calculate_cost_usd


SpanAttrValue = str | int | float | bool | list[str]


@dataclass
class TelemetrySpan:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    kind: str
    start_time_ms: int
    end_time_ms: int = 0
    status: str = "OK"
    attributes: dict[str, SpanAttrValue] = field(default_factory=dict)


class AgentTracer:
    def __init__(self) -> None:
        self._spans: list[TelemetrySpan] = []
        self._seq = 0

    def start_span(
        self,
        trace_id: str,
        name: str,
        kind: str,
        attributes: dict[str, SpanAttrValue],
        parent_span_id: str | None = None,
    ) -> TelemetrySpan:
        self._seq += 1
        span = TelemetrySpan(
            trace_id=trace_id,
            span_id=f"span-{self._seq:04d}",
            parent_span_id=parent_span_id,
            name=name,
            kind=kind,
            start_time_ms=int(time.time() * 1000),
            attributes=dict(attributes),
        )
        self._spans.append(span)
        return span

    def end_span(
        self,
        span: TelemetrySpan,
        status: str = "OK",
        extra: dict[str, SpanAttrValue] | None = None,
    ) -> None:
        span.end_time_ms = int(time.time() * 1000)
        span.status = status
        if extra:
            span.attributes.update(extra)

    def get_trace(self, trace_id: str) -> list[TelemetrySpan]:
        return [s for s in self._spans if s.trace_id == trace_id]


class BudgetCircuitBreaker:
    def __init__(self, max_ticket_cost_usd: float, max_hourly_burn_usd: float) -> None:
        self.max_ticket_cost_usd = max_ticket_cost_usd
        self.max_hourly_burn_usd = max_hourly_burn_usd
        self._hourly_burn_usd = 0.0
        self._window_start = time.time()
        self._tripped = False

    def _reset_window_if_needed(self, now: float) -> None:
        if now - self._window_start >= 3600:
            self._hourly_burn_usd = 0.0
            self._window_start = now
            self._tripped = False

    def check_before_send(self, ticket_cost_usd: float) -> tuple[bool, str | None]:
        self._reset_window_if_needed(time.time())
        if self._tripped or self._hourly_burn_usd >= self.max_hourly_burn_usd:
            self._tripped = True
            return False, "CIRCUIT_OPEN_HOURLY_CAP"
        if ticket_cost_usd >= self.max_ticket_cost_usd:
            return False, f"TICKET_BUDGET_EXCEEDED (${ticket_cost_usd:.4f} >= ${self.max_ticket_cost_usd:.2f})"
        return True, None

    def record_usage(self, ticket_cost_usd: float, turn_cost_usd: float) -> tuple[bool, str | None]:
        self._reset_window_if_needed(time.time())
        self._hourly_burn_usd += turn_cost_usd

        if ticket_cost_usd + turn_cost_usd > self.max_ticket_cost_usd:
            return False, f"TICKET_BUDGET_EXCEEDED (${ticket_cost_usd + turn_cost_usd:.4f} > ${self.max_ticket_cost_usd:.2f})"

        if self._hourly_burn_usd > self.max_hourly_burn_usd:
            self._tripped = True
            return False, f"HOURLY_BURN_EXCEEDED (${self._hourly_burn_usd:.2f} > ${self.max_hourly_burn_usd:.2f})"

        return True, None


def run_observed_turn(
    tracer: AgentTracer,
    breaker: BudgetCircuitBreaker,
    trace_id: str,
    root_span_id: str,
    turn_index: int,
    ticket_cost_so_far: float,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_creation_input_tokens: int,
    cache_read_input_tokens: int,
    stop_reason: str,
) -> tuple[float, float, str | None]:
    turn_span = tracer.start_span(
        trace_id,
        f"turn.{turn_index}",
        "agent.turn",
        {
            "agent.turn_index": turn_index,
            "agent.tenant_id": "tenant-acme",
            "agent.ticket_category": "refund_request",
        },
        root_span_id,
    )
    allowed, reason = breaker.check_before_send(ticket_cost_so_far)
    if not allowed:
        tracer.end_span(turn_span, "ERROR", {"agent.abort_reason": reason or "CIRCUIT_OPEN"})
        return 0.0, 0.0, reason

    total_input = input_tokens + cache_creation_input_tokens + cache_read_input_tokens
    llm_span = tracer.start_span(
        trace_id,
        "anthropic.messages.create",
        "gen_ai.client",
        {
            "gen_ai.provider.name": "anthropic",
            "gen_ai.operation.name": "chat",
            "gen_ai.request.model": model,
            "gen_ai.usage.input_tokens": total_input,
            "gen_ai.usage.output_tokens": output_tokens,
            "gen_ai.usage.cache_creation.input_tokens": cache_creation_input_tokens,
            "gen_ai.usage.cache_read.input_tokens": cache_read_input_tokens,
            "gen_ai.response.finish_reasons": [stop_reason] if stop_reason else [],
        },
        turn_span.span_id,
    )

    turn_cost = calculate_cost_usd(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_creation_input_tokens=cache_creation_input_tokens,
        cache_read_input_tokens=cache_read_input_tokens,
    )
    cache_hit_ratio = (cache_read_input_tokens / total_input) if total_input > 0 else 0.0

    tracer.end_span(
        llm_span,
        "OK",
        {"agent.cost_usd": round(turn_cost, 6), "agent.cache_hit_ratio": round(cache_hit_ratio, 4)},
    )

    if stop_reason == "tool_use":
        tool_span = tracer.start_span(
            trace_id,
            "tool.lookup_order",
            "agent.tool",
            {"agent.tool_name": "lookup_order", "agent.is_error": False},
            turn_span.span_id,
        )
        tracer.end_span(tool_span, "OK")

    allowed, reason = breaker.record_usage(ticket_cost_so_far, turn_cost)
    if not allowed:
        tracer.end_span(turn_span, "ERROR", {"agent.abort_reason": reason or "BUDGET_EXCEEDED"})
        return turn_cost, cache_hit_ratio, reason

    tracer.end_span(turn_span, "OK")
    return turn_cost, cache_hit_ratio, None


def main() -> None:
    tracer = AgentTracer()
    breaker = BudgetCircuitBreaker(max_ticket_cost_usd=0.15, max_hourly_burn_usd=25.0)
    trace_id = "trace-orderops-10492"
    root = tracer.start_span(
        trace_id,
        "orderops.handle_ticket",
        "agent.request",
        {"agent.ticket_id": "TKT-10492", "agent.tenant_id": "tenant-acme"},
    )

    c1, h1, b1 = run_observed_turn(
        tracer, breaker, trace_id, root.span_id, 1, 0.0,
        "claude-sonnet-5-5", 1200, 350, 0, 6800, "tool_use",
    )
    c2, h2, b2 = run_observed_turn(
        tracer, breaker, trace_id, root.span_id, 2, c1,
        "claude-sonnet-5-5", 8000, 350, 0, 0, "end_turn",
    )
    tracer.end_span(root, "ERROR" if (b1 or b2) else "OK", {"agent.total_cost_usd": round(c1 + c2, 6)})

    print("=== OrderOps Telemetry Summary ===")
    print(f"Turn 1 (cached): cost=${c1:.5f}, cache_hit={h1 * 100:.1f}%")
    print(f"Turn 2 (cache miss): cost=${c2:.5f}, cache_hit={h2 * 100:.1f}%")
    print(f"Total spans recorded: {len(tracer.get_trace(trace_id))}")


if __name__ == "__main__":
    main()
