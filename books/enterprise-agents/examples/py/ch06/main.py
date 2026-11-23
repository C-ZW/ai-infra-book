"""Durable execution runner for OrderOps: Checkpoint, Backoff+Jitter, Circuit Breaker, and HITL."""

from __future__ import annotations

import math
import random
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TypeVar

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared.orderops_mock import OrderOpsMockBackend

T = TypeVar("T")


@dataclass(frozen=True)
class CheckpointEvent:
    run_id: str
    seq: int
    step_type: str
    payload: dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InMemoryCheckpointStore:
    def __init__(self) -> None:
        self._events: list[CheckpointEvent] = []

    def append(self, run_id: str, step_type: str, payload: dict[str, Any]) -> CheckpointEvent:
        seq = sum(1 for e in self._events if e.run_id == run_id) + 1
        event = CheckpointEvent(run_id=run_id, seq=seq, step_type=step_type, payload=payload)
        self._events.append(event)
        return event

    def get_events(self, run_id: str) -> list[CheckpointEvent]:
        return sorted((e for e in self._events if e.run_id == run_id), key=lambda e: e.seq)


class RetryableApiError(RuntimeError):
    def __init__(self, message: str, status_code: int, retry_after_sec: float = 0.0) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retry_after_sec = retry_after_sec


def with_backoff_and_jitter(
    fn: Callable[[], T],
    *,
    max_attempts: int = 4,
    base_delay_sec: float = 0.05,
    max_delay_sec: float = 1.0,
) -> T:
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except RetryableApiError as exc:
            last_exc = exc
            if attempt == max_attempts:
                raise
            exp_cap = min(max_delay_sec, base_delay_sec * (2 ** (attempt - 1)))
            full_jitter = random.uniform(0, exp_cap)
            delay = max(full_jitter, exc.retry_after_sec)
            time.sleep(delay)
    assert last_exc is not None
    raise last_exc


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, cooldown_sec: float = 0.2) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_sec = cooldown_sec
        self.state = "closed"
        self.failures = 0
        self.opened_at = 0.0
        self._epoch = 0
        self._half_open_in_flight = False

    def execute(self, fn: Callable[[], T]) -> T:
        if self.state == "open":
            if time.monotonic() - self.opened_at >= self.cooldown_sec:
                self.state = "half_open"
                self._half_open_in_flight = False
            else:
                raise RuntimeError("CircuitBreaker is OPEN; failing fast")

        if self.state == "half_open":
            if self._half_open_in_flight:
                raise RuntimeError("CircuitBreaker is HALF_OPEN; probe in flight")
            self._half_open_in_flight = True

        call_epoch = self._epoch
        try:
            result = fn()
            if call_epoch == self._epoch:
                self.failures = 0
                self.state = "closed"
                self._half_open_in_flight = False
            return result
        except RetryableApiError:
            if call_epoch == self._epoch:
                self.failures += 1
                self._half_open_in_flight = False
                if self.state == "half_open" or self.failures >= self.failure_threshold:
                    self.state = "open"
                    self.opened_at = time.monotonic()
                    self._epoch += 1
            raise
        except Exception:
            if call_epoch == self._epoch:
                self._half_open_in_flight = False
            raise


class DurableOrderOpsRunner:
    def __init__(self) -> None:
        self.store = InMemoryCheckpointStore()
        self.backend = OrderOpsMockBackend()
        self.breaker = CircuitBreaker(failure_threshold=3, cooldown_sec=0.15)

    def run_refund_workflow(
        self,
        *,
        run_id: str,
        refund_operation_id: str,
        order_id: str,
        tenant_id: str,
        amount_usd: float,
        reason: str,
    ) -> dict[str, Any]:
        if not math.isfinite(amount_usd) or amount_usd <= 0:
            raise ValueError("amount_usd must be a positive finite number")
        idempotency_key = f"{tenant_id}:{refund_operation_id}"
        existing = self.store.get_events(run_id)
        completed = next((e for e in existing if e.step_type == "completed"), None)
        if completed is not None:
            return {"status": "completed", "result": completed.payload.get("refund"), "events": existing}

        paused = any(e.step_type == "hitl_pause" for e in existing)
        resumed = any(e.step_type == "hitl_resume" for e in existing)

        if not paused:
            if not any(e.step_type == "llm_turn" for e in existing):
                attempts = 0

                def call_llm() -> dict[str, Any]:
                    nonlocal attempts
                    attempts += 1
                    if attempts == 1:
                        raise RetryableApiError("Rate limit exceeded", 429, retry_after_sec=0.02)
                    return {"action": "issue_refund", "amount_usd": amount_usd}

                decision = self.breaker.execute(lambda: with_backoff_and_jitter(call_llm))
                self.store.append(run_id, "llm_turn", {"decision": decision, "attempts": attempts})

            refund = self.backend.issue_refund(
                order_id=order_id,
                tenant_id=tenant_id,
                amount_usd=amount_usd,
                reason=reason,
                idempotency_key=idempotency_key,
                auto_approve_limit_usd=250.0,
            )
            self.store.append(
                run_id,
                "tool_call",
                {"tool": "issue_refund", "idempotency_key": idempotency_key, "refund": refund},
            )

            if refund["status"] == "pending_hitl":
                self.store.append(
                    run_id,
                    "hitl_pause",
                    {"reason": refund["reason"], "deadline_sec": 3600},
                )
                return {"status": "waiting_hitl", "result": refund, "events": self.store.get_events(run_id)}

            terminal_step = "failed" if refund["status"] == "rejected" else "completed"
            self.store.append(run_id, terminal_step, {"refund": refund})
            return {"status": terminal_step, "result": refund, "events": self.store.get_events(run_id)}

        if paused and not resumed:
            return {"status": "waiting_hitl", "events": existing}

        approved_refund = self.backend.issue_refund(
            order_id=order_id,
            tenant_id=tenant_id,
            amount_usd=amount_usd,
            reason=reason,
            idempotency_key=f"{idempotency_key}:approved",
            auto_approve_limit_usd=10000.0,
        )
        self.store.append(
            run_id,
            "tool_call",
            {"tool": "issue_refund", "idempotency_key": f"{idempotency_key}:approved", "refund": approved_refund},
        )
        self.store.append(run_id, "completed", {"refund": approved_refund})
        return {"status": "completed", "result": approved_refund, "events": self.store.get_events(run_id)}

    def approve_hitl(self, run_id: str, approver: str) -> list[CheckpointEvent]:
        existing = self.store.get_events(run_id)
        is_waiting = any(e.step_type == "hitl_pause" for e in existing) and not any(
            e.step_type in {"hitl_resume", "completed", "failed"} for e in existing
        )
        if not is_waiting:
            raise ValueError(f"Run {run_id} is not waiting for HITL approval")
        self.store.append(run_id, "hitl_resume", {"approved": True, "approver": approver})
        return self.store.get_events(run_id)


def main() -> None:
    runner = DurableOrderOpsRunner()
    first_pass = runner.run_refund_workflow(
        run_id="run-ch06-001",
        refund_operation_id="op-refund-9001",
        order_id="ORD-2026-88412",
        tenant_id="tenant-apac-01",
        amount_usd=300.0,
        reason="Carrier delay SLA compensation",
    )
    print("First pass status:", first_pass["status"])
    print("Checkpoints recorded:", len(first_pass["events"]))

    runner.approve_hitl("run-ch06-001", "ops-lead@example.com")
    resumed_pass = runner.run_refund_workflow(
        run_id="run-ch06-001",
        refund_operation_id="op-refund-9001",
        order_id="ORD-2026-88412",
        tenant_id="tenant-apac-01",
        amount_usd=300.0,
        reason="Carrier delay SLA compensation",
    )
    print("After HITL approval, total checkpoints:", len(resumed_pass["events"]))
    print("Final step:", resumed_pass["events"][-1].step_type)


if __name__ == "__main__":
    main()
