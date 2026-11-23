import { CLAUDE_PRICING_2026_11, calculateCostUsd } from "../shared/types.js";

// ============================================================================
// Scenario B: Enterprise Contract & Compliance Audit Pipeline
// ============================================================================

export interface ContractClause {
  clauseId: string;
  sectionTitle: string;
  text: string;
  tokenEstimate: number;
}

export interface Citation {
  clauseId: string;
  verbatimQuote: string;
}

export interface ClauseRiskFinding {
  clauseId: string;
  severity: "low" | "medium" | "high" | "critical";
  ruleViolated: string;
  rationale: string;
  citations: Citation[];
}

export interface BatchAuditRequest {
  custom_id: string;
  params: {
    model: "claude-sonnet-5-5" | "claude-opus-5-5";
    max_tokens: number;
    thinking: { type: "adaptive" };
    output_config: { effort: "low" | "medium" | "high" };
    messages: Array<{ role: "user"; content: string }>;
  };
}

/**
 * Splits a long contract into indexed clauses without breaking section boundaries.
 * Rejects duplicate clause IDs to prevent silent overwrites.
 */
export function indexContractClauses(rawSections: Array<{ id: string; title: string; body: string }>): ContractClause[] {
  const seen = new Set<string>();
  return rawSections.map((sec) => {
    if (seen.has(sec.id)) {
      throw new Error(`Duplicate clauseId detected: ${sec.id}`);
    }
    seen.add(sec.id);
    return {
      clauseId: sec.id,
      sectionTitle: sec.title,
      text: sec.body.trim(),
      tokenEstimate: Math.ceil(sec.body.length / 3.5),
    };
  });
}

/**
 * Verifies that every finding includes at least one verbatim citation present in the source clause.
 * Rejects ungrounded findings to prevent legal hallucination.
 */
export function validateCitations(
  findings: ClauseRiskFinding[],
  clauseIndex: Map<string, ContractClause>,
): { valid: ClauseRiskFinding[]; rejected: Array<{ clauseId: string; reason: string }> } {
  const valid: ClauseRiskFinding[] = [];
  const rejected: Array<{ clauseId: string; reason: string }> = [];

  for (const f of findings) {
    const source = clauseIndex.get(f.clauseId);
    if (!source) {
      rejected.push({ clauseId: f.clauseId, reason: "clause_not_found" });
      continue;
    }
    if (f.citations.length === 0) {
      rejected.push({ clauseId: f.clauseId, reason: "missing_verbatim_citation" });
      continue;
    }
    const allGrounded = f.citations.every(
      (c) =>
        c.clauseId === f.clauseId &&
        c.verbatimQuote.trim().length > 0 &&
        source.text.includes(c.verbatimQuote),
    );
    if (!allGrounded) {
      rejected.push({ clauseId: f.clauseId, reason: "citation_mismatch_or_fabricated" });
      continue;
    }
    valid.push(f);
  }
  return { valid, rejected };
}

/**
 * Builds a Batch API payload (50% discount on input & output) for overnight compliance scans.
 * Sanitizes custom_id to match ^[a-zA-Z0-9_-]{1,64}$.
 */
export function buildNightlyBatchRequests(
  contractId: string,
  clauses: ContractClause[],
): BatchAuditRequest[] {
  return clauses.map((clause, idx) => {
    const rawId = `${contractId}__${clause.clauseId}__${idx}`;
    const customId = rawId.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 64);
    return {
      custom_id: customId,
      params: {
        model: "claude-sonnet-5-5",
        max_tokens: 4096,
        thinking: { type: "adaptive" },
        output_config: { effort: "medium" },
        messages: [
          {
            role: "user",
            content: `Audit clause ${clause.clauseId} (${clause.sectionTitle}) against enterprise policy:\n\n${clause.text}`,
          },
        ],
      },
    };
  });
}

export function estimateBatchCostUsd(
  model: "claude-sonnet-5-5" | "claude-opus-5-5",
  inputTokens: number,
  outputTokens: number,
): number {
  const standardCost = calculateCostUsd(model, {
    input_tokens: inputTokens,
    output_tokens: outputTokens,
  });
  // Batch API applies a 50% discount to both input and output tokens.
  return standardCost * 0.5;
}

// ============================================================================
// Scenario C: On-Call Triage & PR Review Agent
// ============================================================================

export interface EvidenceRecord {
  source: "logs" | "metrics" | "trace" | "sandbox_repro";
  queryOrCommand: string;
  observedSnippet: string;
  timestamp: string;
}

export interface StructuredPrReview {
  incidentId: string;
  rootCauseSummary: string;
  confidence: "high" | "medium" | "low";
  evidenceChain: EvidenceRecord[];
  sandboxReproPassed: boolean;
  proposedPatchFiles: string[];
}

/**
 * Enforces the anti-hallucination evidence-chain rule:
 * A root cause claim is only accepted if backed by >= 2 distinct read-only telemetry sources
 * AND a deterministic sandbox reproduction.
 */
export function verifyTriageEvidenceChain(review: StructuredPrReview): {
  accepted: boolean;
  reason?: string;
} {
  const telemetrySources = new Set(
    review.evidenceChain
      .filter((e) => e.source !== "sandbox_repro")
      .map((e) => e.source),
  );
  if (telemetrySources.size < 2) {
    return {
      accepted: false,
      reason: `Insufficient telemetry sources (${telemetrySources.size} < 2); possible root-cause hallucination.`,
    };
  }
  const hasSandboxRecord = review.evidenceChain.some((e) => e.source === "sandbox_repro");
  if (!review.sandboxReproPassed || !hasSandboxRecord) {
    return {
      accepted: false,
      reason: "Missing verified sandbox reproduction record or test did not pass; blocking automated PR review.",
    };
  }
  const hasEmptySnippet = review.evidenceChain.some((e) => e.observedSnippet.trim().length === 0);
  if (hasEmptySnippet) {
    return {
      accepted: false,
      reason: "Evidence chain contains empty observedSnippet.",
    };
  }
  return { accepted: true };
}

// ============================================================================
// Runnable Demo
// ============================================================================

function main(): void {
  console.log("=== Scenario B: Contract & Compliance Audit ===");
  const clauses = indexContractClauses([
    {
      id: "C-14.2",
      title: "Limitation of Liability",
      body: "Vendor liability shall not exceed 100% of fees paid in the preceding 12 months, excluding data breach.",
    },
    {
      id: "C-19.1",
      title: "Subprocessor Notice",
      body: "Vendor may appoint subprocessors with 7 days prior written notice to Customer.",
    },
  ]);
  const clauseMap = new Map(clauses.map((c) => [c.clauseId, c]));

  const findings: ClauseRiskFinding[] = [
    {
      clauseId: "C-19.1",
      severity: "high",
      ruleViolated: "POLICY-SUBPROC-30D",
      rationale: "Enterprise policy requires at least 30 days notice for subprocessors.",
      citations: [{ clauseId: "C-19.1", verbatimQuote: "7 days prior written notice" }],
    },
    {
      clauseId: "C-14.2",
      severity: "medium",
      ruleViolated: "POLICY-CAP-200",
      rationale: "Fabricated quote test.",
      citations: [{ clauseId: "C-14.2", verbatimQuote: "unlimited liability" }],
    },
  ];

  const auditResult = validateCitations(findings, clauseMap);
  console.log("Valid findings:", auditResult.valid.length);
  console.log("Rejected findings:", auditResult.rejected);

  const batchReqs = buildNightlyBatchRequests("MSA-2026-089", clauses);
  const sonnetPricing = CLAUDE_PRICING_2026_11["claude-sonnet-5-5"];
  const batchCost = estimateBatchCostUsd("claude-sonnet-5-5", 18_000, 3_500);
  console.log(
    `Batch requests: ${batchReqs.length}, Sonnet standard=$${sonnetPricing.inputPerMTok}/$${sonnetPricing.outputPerMTok}, 50% Batch est=$${batchCost.toFixed(4)}`,
  );

  console.log("\n=== Scenario C: On-Call Triage & PR Review ===");
  const review: StructuredPrReview = {
    incidentId: "INC-4092",
    rootCauseSummary: "Connection pool exhaustion in checkout-worker due to missing timeout on ERP client.",
    confidence: "high",
    sandboxReproPassed: true,
    proposedPatchFiles: ["src/clients/erp-http.ts"],
    evidenceChain: [
      {
        source: "logs",
        queryOrCommand: "service:checkout-worker level:error 'pool timeout'",
        observedSnippet: "ER_POOL_EXHAUSTED: acquired 50/50 connections for >30000ms",
        timestamp: "2026-11-21T02:14:03Z",
      },
      {
        source: "metrics",
        queryOrCommand: "avg(db_pool_active{service='checkout-worker'})",
        observedSnippet: "value=50.0 (limit=50) sustained 12m",
        timestamp: "2026-11-21T02:15:00Z",
      },
      {
        source: "sandbox_repro",
        queryOrCommand: "npm test -- erp-pool-exhaustion.test.ts",
        observedSnippet: "PASS: reproduced hang without timeout, fixed with 5000ms AbortSignal",
        timestamp: "2026-11-21T02:18:22Z",
      },
    ],
  };

  console.log("Triage verification:", verifyTriageEvidenceChain(review));
}

main();
