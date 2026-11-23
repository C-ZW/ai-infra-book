import { CLAUDE_PRICING_2026_11 } from "../shared/types.js";

export type AutonomyLevel = "L1" | "L2" | "L3";

export interface ProductionConfig {
  serviceName: string;
  autonomyLevel: AutonomyLevel;
  triageModel: keyof typeof CLAUDE_PRICING_2026_11;
  workerModel: keyof typeof CLAUDE_PRICING_2026_11;
  inferenceGeo: "global" | "us";
  latencySlo: {
    triageP95Sec: number;
    multiStepP95Sec: number;
  };
  budget: {
    monthlyBudgetCapUsd: number;
    dailyTicketVolume: number;
    estimatedBaseCostPerTicketUsd: number;
  };
  safety: {
    maxTurns: number;
    llmTimeoutMs: number;
    toolTimeoutMs: number;
    wallClockTimeoutMs: number;
    hitlRequiredForMutating: boolean;
    maxAutoRefundUsd: number;
  };
  evalGate: {
    passAt1: number;
    passPow3: number;
  };
  observability: {
    otelEnabled: boolean;
    auditRetentionDays: number;
  };
}

export interface PrrCheckResult {
  gate: string;
  status: "PASS" | "FAIL";
  detail: string;
}

const isPos = (n: number): boolean => Number.isFinite(n) && n > 0;
const isUnitInterval = (n: number): boolean => Number.isFinite(n) && n >= 0 && n <= 1;

export function validateProductionConfig(cfg: ProductionConfig): PrrCheckResult[] {
  const results: PrrCheckResult[] = [];

  // 1. Model registry gate
  const modelsOk =
    Object.prototype.hasOwnProperty.call(CLAUDE_PRICING_2026_11, cfg.triageModel) &&
    Object.prototype.hasOwnProperty.call(CLAUDE_PRICING_2026_11, cfg.workerModel);
  results.push({
    gate: "model_registry",
    status: modelsOk ? "PASS" : "FAIL",
    detail: `triage=${String(cfg.triageModel)}, worker=${String(cfg.workerModel)}`,
  });

  // 2. Latency SLO gate (OrderOps baseline: 2.5s triage, 18s multi-step)
  const sloOk =
    isPos(cfg.latencySlo.triageP95Sec) &&
    isPos(cfg.latencySlo.multiStepP95Sec) &&
    cfg.latencySlo.triageP95Sec <= 2.5 &&
    cfg.latencySlo.multiStepP95Sec <= 18;
  results.push({
    gate: "latency_slo",
    status: sloOk ? "PASS" : "FAIL",
    detail: `triageP95=${cfg.latencySlo.triageP95Sec}s (<=2.5s), multiStepP95=${cfg.latencySlo.multiStepP95Sec}s (<=18s)`,
  });

  // 3. Cost cap gate (OrderOps target: <= $18,000/month including geo multiplier)
  const geoValid = cfg.inferenceGeo === "global" || cfg.inferenceGeo === "us";
  const geoMult = cfg.inferenceGeo === "us" ? 1.1 : 1.0;
  const estMonthlyUsd =
    cfg.budget.dailyTicketVolume * 30 * cfg.budget.estimatedBaseCostPerTicketUsd * geoMult;
  const costOk =
    geoValid &&
    isPos(cfg.budget.monthlyBudgetCapUsd) &&
    isPos(cfg.budget.dailyTicketVolume) &&
    isPos(cfg.budget.estimatedBaseCostPerTicketUsd) &&
    estMonthlyUsd <= cfg.budget.monthlyBudgetCapUsd;
  results.push({
    gate: "cost_cap",
    status: costOk ? "PASS" : "FAIL",
    detail: `est=$${estMonthlyUsd.toFixed(0)}/mo (geo=${cfg.inferenceGeo} ${geoMult}x) <= cap=$${cfg.budget.monthlyBudgetCapUsd}/mo`,
  });

  // 4. Autonomy & HITL gate
  const levelValid = cfg.autonomyLevel === "L1" || cfg.autonomyLevel === "L2" || cfg.autonomyLevel === "L3";
  let autonomyOk = levelValid && typeof cfg.safety.hitlRequiredForMutating === "boolean";
  let autonomyDetail = `level=${String(cfg.autonomyLevel)}`;
  if (cfg.autonomyLevel === "L2" && !cfg.safety.hitlRequiredForMutating) {
    autonomyOk = false;
    autonomyDetail += " requires hitlRequiredForMutating=true";
  }
  if (
    cfg.autonomyLevel === "L3" &&
    (!isPos(cfg.safety.maxAutoRefundUsd) || cfg.safety.maxAutoRefundUsd > 50 || cfg.evalGate.passPow3 < 0.95)
  ) {
    autonomyOk = false;
    autonomyDetail += " requires 0<maxAutoRefundUsd<=50 and pass^3>=0.95";
  }
  results.push({ gate: "autonomy_guardrail", status: autonomyOk ? "PASS" : "FAIL", detail: autonomyDetail });

  // 5. Timeout hierarchy gate: 0 < toolTimeout < llmTimeout < wallClockTimeout
  const timeoutOk =
    isPos(cfg.safety.toolTimeoutMs) &&
    isPos(cfg.safety.llmTimeoutMs) &&
    isPos(cfg.safety.wallClockTimeoutMs) &&
    cfg.safety.toolTimeoutMs < cfg.safety.llmTimeoutMs &&
    cfg.safety.llmTimeoutMs < cfg.safety.wallClockTimeoutMs &&
    Number.isInteger(cfg.safety.maxTurns) &&
    cfg.safety.maxTurns >= 1 &&
    cfg.safety.maxTurns <= 12;
  results.push({
    gate: "timeout_hierarchy",
    status: timeoutOk ? "PASS" : "FAIL",
    detail: `tool=${cfg.safety.toolTimeoutMs}ms < llm=${cfg.safety.llmTimeoutMs}ms < wall=${cfg.safety.wallClockTimeoutMs}ms, maxTurns=${cfg.safety.maxTurns}`,
  });

  // 6. Eval & Observability gate
  const evalOk =
    isUnitInterval(cfg.evalGate.passAt1) &&
    isUnitInterval(cfg.evalGate.passPow3) &&
    cfg.evalGate.passAt1 >= 0.92 &&
    cfg.evalGate.passPow3 >= 0.85;
  results.push({
    gate: "eval_baseline",
    status: evalOk ? "PASS" : "FAIL",
    detail: `Pass@1=${cfg.evalGate.passAt1}, Pass^3=${cfg.evalGate.passPow3}`,
  });

  const obsOk =
    cfg.observability.otelEnabled === true &&
    Number.isInteger(cfg.observability.auditRetentionDays) &&
    cfg.observability.auditRetentionDays >= 90;
  results.push({
    gate: "observability_audit",
    status: obsOk ? "PASS" : "FAIL",
    detail: `otel=${cfg.observability.otelEnabled}, retention=${cfg.observability.auditRetentionDays}d (>=90d)`,
  });

  return results;
}

const candidateConfig: ProductionConfig = {
  serviceName: "orderops-agent-prod",
  autonomyLevel: "L2",
  triageModel: "claude-haiku-5-5",
  workerModel: "claude-sonnet-5-5",
  inferenceGeo: "us",
  latencySlo: { triageP95Sec: 2.1, multiStepP95Sec: 15.4 },
  budget: {
    monthlyBudgetCapUsd: 18_000,
    dailyTicketVolume: 50_000,
    estimatedBaseCostPerTicketUsd: 0.0108,
  },
  safety: {
    maxTurns: 8,
    llmTimeoutMs: 12_000,
    toolTimeoutMs: 5_000,
    wallClockTimeoutMs: 60_000,
    hitlRequiredForMutating: true,
    maxAutoRefundUsd: 0,
  },
  evalGate: { passAt1: 0.94, passPow3: 0.88 },
  observability: { otelEnabled: true, auditRetentionDays: 180 },
};

const checks = validateProductionConfig(candidateConfig);
let failed = 0;
for (const c of checks) {
  console.log(`[${c.status}] ${c.gate}: ${c.detail}`);
  if (c.status === "FAIL") failed++;
}
process.exitCode = failed > 0 ? 1 : 0;
