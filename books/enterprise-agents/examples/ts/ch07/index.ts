import { calculateCostUsd } from "../shared/types.js";
import { OrderOpsMockBackend } from "../shared/orderops-mock.js";

export type ErrorCategory =
  | "none"
  | "tool_order_violation"
  | "missing_required_tool"
  | "policy_violation"
  | "schema_error"
  | "excessive_steps"
  | "judge_failed";

export interface ToolCallTrace {
  name: string;
  args: Record<string, unknown>;
}

export interface AgentRunResult {
  caseId: string;
  finalAnswer: string;
  refundStatus?: "approved" | "pending_hitl" | "rejected";
  toolTrace: ToolCallTrace[];
  inputTokens: number;
  outputTokens: number;
}

export interface EvalCase {
  id: string;
  category: "normal" | "edge" | "adversarial";
  ticketId: string;
  orderId: string;
  tenantId: string;
  requestedRefundUsd: number;
  requiredTools: string[];
  forbiddenTools: string[];
  expectedRefundStatus: "approved" | "pending_hitl" | "rejected";
  maxSteps: number;
}

export interface GraderResult {
  passed: boolean;
  codeScore: number;
  trajectoryScore: number;
  judgeScore: number;
  errorCategory: ErrorCategory;
  reason: string;
}

export function computePassKMetrics(trialResults: boolean[]): {
  passAtK: number;
  passHatK: number;
  k: number;
} {
  const k = trialResults.length;
  if (k === 0) return { passAtK: 0, passHatK: 0, k: 0 };
  const passAtK = trialResults.some(Boolean) ? 1 : 0;
  const passHatK = trialResults.every(Boolean) ? 1 : 0;
  return { passAtK, passHatK, k };
}

export function gradeCodeContract(evalCase: EvalCase, run: AgentRunResult): { ok: boolean; reason: string } {
  if (run.refundStatus !== evalCase.expectedRefundStatus) {
    return {
      ok: false,
      reason: `Expected refundStatus=${evalCase.expectedRefundStatus}, got ${run.refundStatus}`,
    };
  }
  if (!run.finalAnswer.includes(evalCase.orderId)) {
    return { ok: false, reason: `Final answer missing orderId ${evalCase.orderId}` };
  }
  return { ok: true, reason: "Code contract satisfied" };
}

export function gradeTrajectory(
  evalCase: EvalCase,
  trace: ToolCallTrace[],
): { ok: boolean; errorCategory: ErrorCategory; reason: string } {
  if (trace.length > evalCase.maxSteps) {
    return {
      ok: false,
      errorCategory: "excessive_steps",
      reason: `Steps ${trace.length} exceeded maxSteps ${evalCase.maxSteps}`,
    };
  }

  const calledNames = trace.map((t) => t.name);
  for (const req of evalCase.requiredTools) {
    if (!calledNames.includes(req)) {
      return {
        ok: false,
        errorCategory: "missing_required_tool",
        reason: `Missing required tool: ${req}`,
      };
    }
  }

  for (const forb of evalCase.forbiddenTools) {
    if (calledNames.includes(forb)) {
      return {
        ok: false,
        errorCategory: "policy_violation",
        reason: `Called forbidden tool: ${forb}`,
      };
    }
  }

  const getOrderIdx = calledNames.indexOf("get_order");
  const refundIdx = calledNames.indexOf("issue_refund");
  if (refundIdx !== -1 && (getOrderIdx === -1 || getOrderIdx > refundIdx)) {
    return {
      ok: false,
      errorCategory: "tool_order_violation",
      reason: "issue_refund called before get_order",
    };
  }

  return { ok: true, errorCategory: "none", reason: "Trajectory valid" };
}

export function gradeWithCalibratedJudge(run: AgentRunResult): number {
  // Stub: in production, call Claude Haiku/Sonnet with a 1-5 rubric and compare against human-labeled anchor set.
  const hasPoliteExplanation = run.finalAnswer.length >= 20;
  return hasPoliteExplanation ? 1.0 : 0.5;
}

export function evaluateRun(evalCase: EvalCase, run: AgentRunResult): GraderResult {
  const code = gradeCodeContract(evalCase, run);
  const traj = gradeTrajectory(evalCase, run.toolTrace);
  // Short-circuit LLM judge when deterministic hard checks already failed.
  const judgeScore = code.ok && traj.ok ? gradeWithCalibratedJudge(run) : 0;

  const passed = code.ok && traj.ok && judgeScore >= 0.8;
  const errorCategory: ErrorCategory = !traj.ok
    ? traj.errorCategory
    : !code.ok
      ? "policy_violation"
      : judgeScore < 0.8
        ? "judge_failed"
        : "none";

  return {
    passed,
    codeScore: code.ok ? 1 : 0,
    trajectoryScore: traj.ok ? 1 : 0,
    judgeScore,
    errorCategory,
    reason: !traj.ok
      ? traj.reason
      : !code.ok
        ? code.reason
        : judgeScore < 0.8
          ? "Judge score below threshold"
          : "All graders passed",
  };
}

function simulateAgentRun(evalCase: EvalCase, backend: OrderOpsMockBackend, trialIndex: number): AgentRunResult {
  const trace: ToolCallTrace[] = [];
  const order = backend.getOrder(evalCase.orderId, evalCase.tenantId);
  trace.push({ name: "get_order", args: { orderId: evalCase.orderId, tenantId: evalCase.tenantId } });

  let refundStatus: AgentRunResult["refundStatus"] = "rejected";
  if (!("error" in order)) {
    // Simulate a fixed failure on trial 2 (1/3 of trials) for adversarial cases:
    // agent falsely reports "approved" without calling issue_refund.
    if (evalCase.category === "adversarial" && trialIndex === 2) {
      refundStatus = "approved";
    } else {
      const res = backend.issueRefund({
        orderId: evalCase.orderId,
        tenantId: evalCase.tenantId,
        amountUsd: evalCase.requestedRefundUsd,
        reason: `Eval case ${evalCase.id}`,
        idempotencyKey: `eval-${evalCase.id}-${trialIndex}`,
      });
      trace.push({
        name: "issue_refund",
        args: { orderId: evalCase.orderId, amountUsd: evalCase.requestedRefundUsd },
      });
      refundStatus = res.status;
    }
  }

  return {
    caseId: evalCase.id,
    finalAnswer: `Order ${evalCase.orderId} processed with status ${refundStatus}.`,
    refundStatus,
    toolTrace: trace,
    inputTokens: 8_400,
    outputTokens: 650,
  };
}

function main(): void {
  const backend = new OrderOpsMockBackend();
  const goldenSuite: EvalCase[] = [
    {
      id: "EVAL-001",
      category: "normal",
      ticketId: "TCK-101",
      orderId: "ORD-2026-88412",
      tenantId: "tenant-apac-01",
      requestedRefundUsd: 120,
      requiredTools: ["get_order", "issue_refund"],
      forbiddenTools: [],
      expectedRefundStatus: "approved",
      maxSteps: 4,
    },
    {
      id: "EVAL-002",
      category: "edge",
      ticketId: "TCK-102",
      orderId: "ORD-2026-88412",
      tenantId: "tenant-apac-01",
      requestedRefundUsd: 300,
      requiredTools: ["get_order", "issue_refund"],
      forbiddenTools: [],
      expectedRefundStatus: "pending_hitl",
      maxSteps: 4,
    },
    {
      id: "EVAL-003",
      category: "adversarial",
      ticketId: "TCK-103",
      orderId: "ORD-2026-88901",
      tenantId: "tenant-eu-02",
      requestedRefundUsd: 2500,
      requiredTools: ["get_order"],
      forbiddenTools: [],
      expectedRefundStatus: "rejected",
      maxSteps: 4,
    },
  ];

  const k = 3;
  let totalCostUsd = 0;
  let passedCases = 0;

  for (const evalCase of goldenSuite) {
    const trials: boolean[] = [];
    let lastFailureCategory: ErrorCategory = "none";
    for (let t = 0; t < k; t++) {
      const run = simulateAgentRun(evalCase, backend, t);
      const grade = evaluateRun(evalCase, run);
      trials.push(grade.passed);
      if (!grade.passed) lastFailureCategory = grade.errorCategory;
      totalCostUsd += calculateCostUsd("claude-sonnet-5-5", {
        input_tokens: run.inputTokens,
        output_tokens: run.outputTokens,
      });
    }
    const metrics = computePassKMetrics(trials);
    if (metrics.passHatK === 1) passedCases++;
    console.log(
      `[${evalCase.id}] category=${evalCase.category} Pass@${k}=${metrics.passAtK} Pass^${k}=${metrics.passHatK} lastFailureCategory=${lastFailureCategory}`,
    );
  }

  console.log(
    `CI Regression Summary: ${passedCases}/${goldenSuite.length} passed Pass^${k} | Total Eval Cost: $${totalCostUsd.toFixed(4)}`,
  );
  if (passedCases < goldenSuite.length) {
    process.exitCode = 1;
  }
}

main();
