"""Chapter 11 runnable skeletons for Scenario B (Contract Audit) and Scenario C (On-Call Triage)."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# Ensure shared package is importable when running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.types import CLAUDE_PRICING_2026_11, calculate_cost_usd  # noqa: E402


# ============================================================================
# Scenario B: Enterprise Contract & Compliance Audit Pipeline
# ============================================================================


@dataclass(frozen=True)
class ContractClause:
    clause_id: str
    section_title: str
    text: str
    token_estimate: int


@dataclass(frozen=True)
class Citation:
    clause_id: str
    verbatim_quote: str


@dataclass(frozen=True)
class ClauseRiskFinding:
    clause_id: str
    severity: Literal["low", "medium", "high", "critical"]
    rule_violated: str
    rationale: str
    citations: list[Citation]


def index_contract_clauses(raw_sections: list[dict[str, str]]) -> list[ContractClause]:
    seen: set[str] = set()
    clauses: list[ContractClause] = []
    for sec in raw_sections:
        cid = sec["id"]
        if cid in seen:
            raise ValueError(f"Duplicate clause_id detected: {cid}")
        seen.add(cid)
        clauses.append(
            ContractClause(
                clause_id=cid,
                section_title=sec["title"],
                text=sec["body"].strip(),
                token_estimate=max(1, int(len(sec["body"]) / 3.5)),
            )
        )
    return clauses


def validate_citations(
    findings: list[ClauseRiskFinding],
    clause_index: dict[str, ContractClause],
) -> tuple[list[ClauseRiskFinding], list[dict[str, str]]]:
    valid: list[ClauseRiskFinding] = []
    rejected: list[dict[str, str]] = []

    for finding in findings:
        source = clause_index.get(finding.clause_id)
        if source is None:
            rejected.append({"clause_id": finding.clause_id, "reason": "clause_not_found"})
            continue
        if not finding.citations:
            rejected.append({"clause_id": finding.clause_id, "reason": "missing_verbatim_citation"})
            continue
        all_grounded = all(
            c.clause_id == finding.clause_id
            and len(c.verbatim_quote.strip()) > 0
            and c.verbatim_quote in source.text
            for c in finding.citations
        )
        if not all_grounded:
            rejected.append({"clause_id": finding.clause_id, "reason": "citation_mismatch_or_fabricated"})
            continue
        valid.append(finding)

    return valid, rejected


def build_nightly_batch_requests(
    contract_id: str,
    clauses: list[ContractClause],
) -> list[dict[str, object]]:
    requests: list[dict[str, object]] = []
    for idx, clause in enumerate(clauses):
        raw_id = f"{contract_id}__{clause.clause_id}__{idx}"
        custom_id = re.sub(r"[^a-zA-Z0-9_-]", "_", raw_id)[:64]
        requests.append(
            {
                "custom_id": custom_id,
                "params": {
                    "model": "claude-sonnet-5-5",
                    "max_tokens": 4096,
                    "thinking": {"type": "adaptive"},
                    "output_config": {"effort": "medium"},
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                f"Audit clause {clause.clause_id} ({clause.section_title}) "
                                f"against enterprise policy:\n\n{clause.text}"
                            ),
                        }
                    ],
                },
            }
        )
    return requests


def estimate_batch_cost_usd(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    standard = calculate_cost_usd(model, input_tokens=input_tokens, output_tokens=output_tokens)
    return standard * 0.5  # Batch API 50% discount


# ============================================================================
# Scenario C: On-Call Triage & PR Review Agent
# ============================================================================


@dataclass(frozen=True)
class EvidenceRecord:
    source: Literal["logs", "metrics", "trace", "sandbox_repro"]
    query_or_command: str
    observed_snippet: str
    timestamp: str


@dataclass(frozen=True)
class StructuredPrReview:
    incident_id: str
    root_cause_summary: str
    confidence: Literal["high", "medium", "low"]
    evidence_chain: list[EvidenceRecord]
    sandbox_repro_passed: bool
    proposed_patch_files: list[str]


def verify_triage_evidence_chain(review: StructuredPrReview) -> tuple[bool, str]:
    telemetry_sources = {e.source for e in review.evidence_chain if e.source != "sandbox_repro"}
    if len(telemetry_sources) < 2:
        return False, f"Insufficient telemetry sources ({len(telemetry_sources)} < 2)."
    has_sandbox_record = any(e.source == "sandbox_repro" for e in review.evidence_chain)
    if not review.sandbox_repro_passed or not has_sandbox_record:
        return False, "Missing verified sandbox reproduction record or test did not pass; blocking automated PR review."
    if any(not e.observed_snippet.strip() for e in review.evidence_chain):
        return False, "Evidence chain contains empty observed_snippet."
    return True, "ok"


def main() -> None:
    print("=== Scenario B: Contract & Compliance Audit ===")
    clauses = index_contract_clauses(
        [
            {
                "id": "C-14.2",
                "title": "Limitation of Liability",
                "body": "Vendor liability shall not exceed 100% of fees paid in the preceding 12 months, excluding data breach.",
            },
            {
                "id": "C-19.1",
                "title": "Subprocessor Notice",
                "body": "Vendor may appoint subprocessors with 7 days prior written notice to Customer.",
            },
        ]
    )
    clause_map = {c.clause_id: c for c in clauses}

    findings = [
        ClauseRiskFinding(
            clause_id="C-19.1",
            severity="high",
            rule_violated="POLICY-SUBPROC-30D",
            rationale="Enterprise policy requires at least 30 days notice for subprocessors.",
            citations=[Citation(clause_id="C-19.1", verbatim_quote="7 days prior written notice")],
        ),
        ClauseRiskFinding(
            clause_id="C-14.2",
            severity="medium",
            rule_violated="POLICY-CAP-200",
            rationale="Fabricated quote test.",
            citations=[Citation(clause_id="C-14.2", verbatim_quote="unlimited liability")],
        ),
    ]

    valid, rejected = validate_citations(findings, clause_map)
    print(f"Valid findings: {len(valid)}, Rejected: {rejected}")

    batch_reqs = build_nightly_batch_requests("MSA-2026-089", clauses)
    pricing = CLAUDE_PRICING_2026_11["claude-sonnet-5-5"]
    batch_cost = estimate_batch_cost_usd("claude-sonnet-5-5", 18_000, 3_500)
    print(
        f"Batch requests: {len(batch_reqs)}, Sonnet standard=${pricing.input_per_mtok}/${pricing.output_per_mtok}, "
        f"50% Batch est=${batch_cost:.4f}"
    )

    print("\n=== Scenario C: On-Call Triage & PR Review ===")
    review = StructuredPrReview(
        incident_id="INC-4092",
        root_cause_summary="Connection pool exhaustion in checkout-worker due to missing timeout on ERP client.",
        confidence="high",
        sandbox_repro_passed=True,
        proposed_patch_files=["src/clients/erp-http.ts"],
        evidence_chain=[
            EvidenceRecord(
                source="logs",
                query_or_command="service:checkout-worker level:error 'pool timeout'",
                observed_snippet="ER_POOL_EXHAUSTED: acquired 50/50 connections for >30000ms",
                timestamp="2026-11-21T02:14:03Z",
            ),
            EvidenceRecord(
                source="metrics",
                query_or_command="avg(db_pool_active{service='checkout-worker'})",
                observed_snippet="value=50.0 (limit=50) sustained 12m",
                timestamp="2026-11-21T02:15:00Z",
            ),
            EvidenceRecord(
                source="sandbox_repro",
                query_or_command="pytest tests/test_erp_pool_exhaustion.py",
                observed_snippet="PASSED: reproduced hang without timeout, fixed with 5000ms timeout",
                timestamp="2026-11-21T02:18:22Z",
            ),
        ],
    )
    print("Triage verification:", verify_triage_evidence_chain(review))


if __name__ == "__main__":
    main()
