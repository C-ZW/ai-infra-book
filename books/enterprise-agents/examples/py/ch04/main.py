"""Chapter 4: Persistent Session State, Multi-Tenant Hybrid Search, and Citation Verification."""

from __future__ import annotations

import json
import math
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared.types import calculate_cost_usd  # noqa: E402


class VersionConflictError(RuntimeError):
    """Raised when optimistic locking detects a concurrent state update."""


@dataclass
class AgentSessionState:
    session_id: str
    tenant_id: str
    ticket_id: str
    status: str  # "active" | "waiting_external" | "completed" | "expired"
    turn_count: int
    version: int
    messages: list[dict]
    waiting_for: str | None = None
    expires_at: str | None = None


class SQLiteSessionStore:
    """SQLite-backed session store mirroring PostgreSQL JSONB + tenant isolation + version CAS."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_sessions (
                tenant_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                ticket_id TEXT NOT NULL,
                status TEXT NOT NULL,
                turn_count INTEGER NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                messages_json TEXT NOT NULL,
                waiting_for TEXT,
                expires_at TEXT NOT NULL,
                PRIMARY KEY (tenant_id, session_id)
            )
            """
        )
        self.conn.commit()

    def save(
        self,
        state: AgentSessionState,
        ttl_hours: int | None = None,
        expected_version: int | None = None,
    ) -> AgentSessionState:
        now = datetime.now(timezone.utc)
        expires_at = (
            (now + timedelta(hours=ttl_hours)).isoformat()
            if ttl_hours is not None
            else (state.expires_at or (now + timedelta(hours=24)).isoformat())
        )

        if expected_version is not None:
            cur = self.conn.execute(
                """
                UPDATE agent_sessions
                SET status = ?, turn_count = ?, version = version + 1,
                    messages_json = ?, waiting_for = ?, expires_at = ?
                WHERE tenant_id = ? AND session_id = ? AND version = ?
                """,
                (
                    state.status,
                    state.turn_count,
                    json.dumps(state.messages),
                    state.waiting_for,
                    expires_at,
                    state.tenant_id,
                    state.session_id,
                    expected_version,
                ),
            )
            self.conn.commit()
            if cur.rowcount != 1:
                raise VersionConflictError(
                    f"Optimistic lock conflict on {state.session_id} (expected version {expected_version})"
                )
            return AgentSessionState(
                session_id=state.session_id,
                tenant_id=state.tenant_id,
                ticket_id=state.ticket_id,
                status=state.status,
                turn_count=state.turn_count,
                version=expected_version + 1,
                messages=list(state.messages),
                waiting_for=state.waiting_for,
                expires_at=expires_at,
            )

        self.conn.execute(
            """
            INSERT INTO agent_sessions (
                tenant_id, session_id, ticket_id, status, turn_count, version, messages_json, waiting_for, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(tenant_id, session_id) DO UPDATE SET
                status = excluded.status,
                turn_count = excluded.turn_count,
                version = agent_sessions.version + 1,
                messages_json = excluded.messages_json,
                waiting_for = excluded.waiting_for,
                expires_at = excluded.expires_at
            """,
            (
                state.tenant_id,
                state.session_id,
                state.ticket_id,
                state.status,
                state.turn_count,
                state.version,
                json.dumps(state.messages),
                state.waiting_for,
                expires_at,
            ),
        )
        self.conn.commit()
        return AgentSessionState(
            session_id=state.session_id,
            tenant_id=state.tenant_id,
            ticket_id=state.ticket_id,
            status=state.status,
            turn_count=state.turn_count,
            version=state.version,
            messages=list(state.messages),
            waiting_for=state.waiting_for,
            expires_at=expires_at,
        )

    def load(self, tenant_id: str, session_id: str) -> AgentSessionState | None:
        row = self.conn.execute(
            """
            SELECT ticket_id, status, turn_count, version, messages_json, waiting_for, expires_at
            FROM agent_sessions
            WHERE tenant_id = ? AND session_id = ?
            """,
            (tenant_id, session_id),
        ).fetchone()
        if row is None:
            return None
        ticket_id, status, turn_count, version, messages_json, waiting_for, expires_at = row
        if datetime.now(timezone.utc) > datetime.fromisoformat(expires_at):
            status = "expired"
        return AgentSessionState(
            session_id=session_id,
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            status=status,
            turn_count=turn_count,
            version=version,
            messages=json.loads(messages_json),
            waiting_for=waiting_for,
            expires_at=expires_at,
        )


@dataclass(frozen=True)
class KnowledgeChunk:
    doc_id: str
    clause_id: str
    tenant_id: str
    acl_roles: tuple[str, ...]
    title: str
    content: str
    terms: tuple[str, ...]
    embedding: tuple[float, float, float, float]


CORPUS: list[KnowledgeChunk] = [
    KnowledgeChunk(
        doc_id="POL-RET-APAC",
        clause_id="4.2",
        tenant_id="tenant-apac-01",
        acl_roles=("ops_agent", "supervisor"),
        title="APAC Delayed Shipment Compensation",
        content="If carrier delay exceeds 72 hours past promisedDeliveryDate, approve up to $250 USD goodwill refund without HITL.",
        terms=("delay", "carrier", "72", "hours", "refund", "250", "apac", "goodwill"),
        embedding=(0.85, 0.90, 0.10, 0.05),
    ),
    KnowledgeChunk(
        doc_id="POL-SUP-SLA",
        clause_id="2.1",
        tenant_id="global",
        acl_roles=("ops_agent", "supervisor"),
        title="Global Supplier Escalation SLA",
        content="When waiting for supplier confirmation, pause session state for up to 24 hours before escalating to supervisor.",
        terms=("supplier", "pause", "session", "24", "hours", "escalate", "sla"),
        embedding=(0.55, 0.10, 0.95, 0.05),
    ),
    KnowledgeChunk(
        doc_id="POL-VIP-EU",
        clause_id="9.1",
        tenant_id="tenant-eu-02",
        acl_roles=("supervisor",),
        title="EU-02 Confidential Margin Rebate",
        content="Confidential EU-02 wholesale rebate is 18% on SKU-PRO-900.",
        terms=("eu-02", "rebate", "18%", "confidential", "sku-pro-900", "refund"),
        embedding=(0.05, 0.40, 0.05, 0.95),
    ),
]


def _cosine_similarity(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    denom = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return 0.0 if denom == 0 else dot / denom


def _embed_query(query_terms: set[str]) -> tuple[float, float, float, float]:
    def has(words: set[str]) -> float:
        return 0.9 if (query_terms & words) else 0.0

    return (
        has({"delay", "carrier", "72", "hours", "sla"}),
        has({"refund", "250", "goodwill", "rebate"}),
        has({"supplier", "pause", "escalate"}),
        has({"eu-02", "rebate", "wholesale"}),
    )


def hybrid_search(
    query: str,
    tenant_id: str,
    caller_roles: set[str],
    top_k: int = 3,
) -> list[tuple[KnowledgeChunk, float]]:
    """Pre-filtered Hybrid Search (BM25 + Vector Cosine + RRF)."""
    bounded_k = min(20, max(1, int(top_k)))
    query_terms = [t for t in re.split(r"[^\w-]+", query.lower()) if len(t) > 1]
    if not query_terms:
        return []

    # Mandatory ACL pre-filtering before any scoring
    authorized = [
        c
        for c in CORPUS
        if (c.tenant_id == tenant_id or c.tenant_id == "global")
        and any(r in caller_roles for r in c.acl_roles)
    ]
    if not authorized:
        return []

    k1, b = 1.2, 0.75
    avg_dl = sum(len(c.terms) for c in authorized) / len(authorized)
    q_vec = _embed_query(set(query_terms))

    bm25_scores: dict[str, float] = {}
    vec_scores: dict[str, float] = {}
    for chunk in authorized:
        cid = f"{chunk.doc_id}#{chunk.clause_id}"
        bm25 = 0.0
        dl = len(chunk.terms)
        for term in set(query_terms):
            tf = chunk.terms.count(term)
            if tf == 0:
                continue
            df = sum(1 for c in authorized if term in c.terms)
            idf = math.log(1.0 + (len(authorized) - df + 0.5) / (df + 0.5))
            tf_norm = (tf * (k1 + 1.0)) / (tf + k1 * (1.0 - b + b * (dl / avg_dl)))
            bm25 += idf * tf_norm
        bm25_scores[cid] = bm25
        vec_scores[cid] = _cosine_similarity(q_vec, chunk.embedding)

    bm25_ranked = [
        f"{c.doc_id}#{c.clause_id}"
        for c in sorted(authorized, key=lambda c: bm25_scores[f"{c.doc_id}#{c.clause_id}"], reverse=True)
        if bm25_scores[f"{c.doc_id}#{c.clause_id}"] > 0
    ]
    vec_ranked = [
        f"{c.doc_id}#{c.clause_id}"
        for c in sorted(authorized, key=lambda c: vec_scores[f"{c.doc_id}#{c.clause_id}"], reverse=True)
        if vec_scores[f"{c.doc_id}#{c.clause_id}"] > 0
    ]

    rrf_k = 60
    scores: list[tuple[KnowledgeChunk, float]] = []
    for chunk in authorized:
        cid = f"{chunk.doc_id}#{chunk.clause_id}"
        r1 = (1.0 / (rrf_k + bm25_ranked.index(cid) + 1)) if cid in bm25_ranked else 0.0
        r2 = (1.0 / (rrf_k + vec_ranked.index(cid) + 1)) if cid in vec_ranked else 0.0
        rrf = r1 + r2
        if rrf > 0:
            scores.append((chunk, rrf))

    scores.sort(key=lambda x: (-x[1], f"{x[0].doc_id}#{x[0].clause_id}"))
    return scores[:bounded_k]


def verify_citations(
    answer_text: str,
    retrieved: list[tuple[KnowledgeChunk, float]],
    require_citation: bool = True,
) -> dict:
    allowed = {f"{c.doc_id}#{c.clause_id}" for c, _ in retrieved}
    cited = re.findall(r"\[([A-Za-z0-9-]+#[0-9.]+)\]", answer_text)
    fabricated = [c for c in cited if c not in allowed]
    missing_citation = require_citation and len(cited) == 0
    return {
        "valid": (not missing_citation) and len(fabricated) == 0,
        "cited": cited,
        "fabricated": fabricated,
        "missing_citation": missing_citation,
    }


def main() -> None:
    store = SQLiteSessionStore()
    store.save(
        AgentSessionState(
            session_id="sess-88412",
            tenant_id="tenant-apac-01",
            ticket_id="TKT-88412",
            status="waiting_external",
            turn_count=2,
            version=1,
            messages=[{"role": "user", "content": "Order ORD-2026-88412 delayed > 72h."}],
            waiting_for="supplier_eta_webhook",
        ),
        ttl_hours=24,
    )

    loaded = store.load("tenant-apac-01", "sess-88412")
    assert loaded is not None and loaded.status != "expired"
    updated = store.save(
        AgentSessionState(
            session_id=loaded.session_id,
            tenant_id=loaded.tenant_id,
            ticket_id=loaded.ticket_id,
            status="active",
            turn_count=loaded.turn_count + 1,
            version=loaded.version,
            messages=loaded.messages,
            waiting_for=None,
            expires_at=loaded.expires_at,
        ),
        expected_version=loaded.version,
    )
    reloaded = store.load("tenant-apac-01", "sess-88412")
    assert reloaded is not None

    conflict_caught = False
    try:
        store.save(loaded, expected_version=loaded.version)
    except VersionConflictError:
        conflict_caught = True

    results = hybrid_search(
        query="carrier delay 72 hours refund policy",
        tenant_id=reloaded.tenant_id,
        caller_roles={"ops_agent"},
        top_k=3,
    )
    print(
        "Resumed session:",
        reloaded.session_id,
        "turn:",
        reloaded.turn_count,
        "version:",
        updated.version,
        "conflict_caught:",
        conflict_caught,
    )
    print("Authorized chunks:", [f"{c.doc_id}#{c.clause_id}" for c, _ in results])

    good = "Per [POL-RET-APAC#4.2], approve up to $250 USD goodwill refund."
    bad = "Per [POL-VIP-EU#9.1], apply 18% wholesale rebate."
    uncited = "Approve up to $250 USD goodwill refund."
    print("Good citation check:", verify_citations(good, results))
    print("Bad citation check:", verify_citations(bad, results))
    print("Uncited check:", verify_citations(uncited, results))

    chunk_input_cost = calculate_cost_usd("claude-sonnet-5-5", input_tokens=1800, output_tokens=0)
    rag_turn_cost = calculate_cost_usd("claude-sonnet-5-5", input_tokens=1800, output_tokens=350)
    print(f"Retrieved chunks input cost (USD): {chunk_input_cost:.6f}")
    print(f"Single Agentic RAG turn cost incl. 350 output tokens (USD): {rag_turn_cost:.6f}")


if __name__ == "__main__":
    main()
