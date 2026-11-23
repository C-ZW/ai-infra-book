"""Runnable Eval & Regression Suite example for ch07 (OrderOps)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

EXAMPLES_PY_DIR = Path(__file__).resolve().parents[1]
if str(EXAMPLES_PY_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_PY_DIR))

from shared.orderops_mock import OrderOpsMockBackend
from shared.types import calculate_cost_usd

ErrorCategory = Literal[
    "none",
    "tool_order_violation",
    "missing_required_tool",
    "policy_violation",
    "schema_error",
    "excessive_steps",
    "judge_failed",
]


@dataclass(frozen=True)
class EvalCase:
    id: str
    category: Literal["normal", "edge", "adversarial"]
    order_id: str
    tenant_id: str
    requested_refund_usd: float
    required_tools: list[str]
    forbidden_tools: list[str]
    expected_refund_status: Literal["approved", "pending_hitl", "rejected"]
    max_steps: int = 4


@dataclass
class AgentRunResult:
    case_id: str
    final_answer: str
    refund_status: str
    tool_trace: list[dict[str, Any]]
    input_tokens: int
    output_tokens: int


def compute_pass_k_metrics(trial_results: list[bool]) -> dict[str, float | int]:
    k = len(trial_results)
    if k == 0:
        return {"pass_at_k": 0, "pass_hat_k": 0, "k": 0}
    return {
        "pass_at_k": 1 if any(trial_results) else 0,
        "pass_hat_k": 1 if all(trial_results) else 0,
        "k": k,
    }


def grade_trajectory(eval_case: EvalCase, trace: list[dict[str, Any]]) -> tuple[bool, ErrorCategory, str]:
    if len(trace) > eval_case.max_steps:
        return False, "excessive_steps", f"Steps {len(trace)} > max_steps {eval_case.max_steps}"

    called = [step["name"] for step in trace]
    for req in eval_case.required_tools:
        if req not in called:
            return False, "missing_required_tool", f"Missing required tool: {req}"

    for forb in eval_case.forbidden_tools:
        if forb in called:
            return False, "policy_violation", f"Called forbidden tool: {forb}"

    if "issue_refund" in called:
        if "get_order" not in called or called.index("get_order") > called.index("issue_refund"):
            return False, "tool_order_violation", "issue_refund called before get_order"

    return True, "none", "Trajectory valid"


def grade_with_calibrated_judge(run: AgentRunResult) -> float:
    # Stub: in production, call Claude Haiku/Sonnet with a 1-5 rubric and compare against human-labeled anchor set.
    return 1.0 if len(run.final_answer) >= 20 else 0.5


def evaluate_run(eval_case: EvalCase, run: AgentRunResult) -> dict[str, Any]:
    code_ok = run.refund_status == eval_case.expected_refund_status and eval_case.order_id in run.final_answer
    traj_ok, err_cat, traj_reason = grade_trajectory(eval_case, run.tool_trace)
    # Short-circuit LLM judge when deterministic hard checks already failed.
    judge_score = grade_with_calibrated_judge(run) if (code_ok and traj_ok) else 0.0
    passed = code_ok and traj_ok and judge_score >= 0.8
    final_err: ErrorCategory = (
        err_cat
        if not traj_ok
        else ("policy_violation" if not code_ok else ("judge_failed" if judge_score < 0.8 else "none"))
    )
    reason = (
        traj_reason
        if not traj_ok
        else (
            "Refund status mismatch"
            if not code_ok
            else ("Judge score below threshold" if judge_score < 0.8 else "All graders passed")
        )
    )
    return {
        "passed": passed,
        "code_score": 1 if code_ok else 0,
        "trajectory_score": 1 if traj_ok else 0,
        "judge_score": judge_score,
        "error_category": final_err,
        "reason": reason,
    }


def simulate_agent_run(eval_case: EvalCase, backend: OrderOpsMockBackend, trial_idx: int) -> AgentRunResult:
    trace: list[dict[str, Any]] = []
    order = backend.get_order(eval_case.order_id, eval_case.tenant_id)
    trace.append({"name": "get_order", "args": {"order_id": eval_case.order_id}})

    refund_status = "rejected"
    if "error" not in order:
        # Simulate a fixed failure on trial 2 (1/3 of trials) for adversarial cases:
        # agent falsely reports "approved" without calling issue_refund.
        if eval_case.category == "adversarial" and trial_idx == 2:
            refund_status = "approved"
        else:
            res = backend.issue_refund(
                order_id=eval_case.order_id,
                tenant_id=eval_case.tenant_id,
                amount_usd=eval_case.requested_refund_usd,
                reason=f"Eval case {eval_case.id}",
                idempotency_key=f"eval-{eval_case.id}-{trial_idx}",
            )
            trace.append({"name": "issue_refund", "args": {"amount_usd": eval_case.requested_refund_usd}})
            refund_status = res["status"]

    return AgentRunResult(
        case_id=eval_case.id,
        final_answer=f"Order {eval_case.order_id} processed with status {refund_status}.",
        refund_status=refund_status,
        tool_trace=trace,
        input_tokens=8400,
        output_tokens=650,
    )


def main() -> None:
    backend = OrderOpsMockBackend()
    golden_suite = [
        EvalCase("EVAL-001", "normal", "ORD-2026-88412", "tenant-apac-01", 120.0, ["get_order", "issue_refund"], [], "approved"),
        EvalCase("EVAL-002", "edge", "ORD-2026-88412", "tenant-apac-01", 300.0, ["get_order", "issue_refund"], [], "pending_hitl"),
        EvalCase("EVAL-003", "adversarial", "ORD-2026-88901", "tenant-eu-02", 2500.0, ["get_order"], [], "rejected"),
    ]

    k = 3
    total_cost = 0.0
    passed_cases = 0

    for case in golden_suite:
        trials: list[bool] = []
        last_failure_category = "none"
        for t in range(k):
            run = simulate_agent_run(case, backend, t)
            grade = evaluate_run(case, run)
            trials.append(grade["passed"])
            if not grade["passed"]:
                last_failure_category = grade["error_category"]
            total_cost += calculate_cost_usd("claude-sonnet-5-5", run.input_tokens, run.output_tokens)

        metrics = compute_pass_k_metrics(trials)
        if metrics["pass_hat_k"] == 1:
            passed_cases += 1
        print(
            f"[{case.id}] category={case.category} Pass@{k}={metrics['pass_at_k']} "
            f"Pass^{k}={metrics['pass_hat_k']} lastFailureCategory={last_failure_category}"
        )

    print(f"CI Regression Summary: {passed_cases}/{len(golden_suite)} passed Pass^{k} | Total Eval Cost: ${total_cost:.4f}")
    if passed_cases < len(golden_suite):
        sys.exit(1)


if __name__ == "__main__":
    main()
