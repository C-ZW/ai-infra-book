import { calculateCostUsd } from "../shared/types.js";

export type SessionStatus = "active" | "waiting_external" | "completed" | "expired";

export interface StoredMessage {
  role: "user" | "assistant";
  content: unknown;
  createdAt: string;
}

export interface AgentSessionState {
  sessionId: string;
  tenantId: string;
  ticketId: string;
  status: SessionStatus;
  turnCount: number;
  version: number;
  messages: StoredMessage[];
  waitingFor?: string;
  updatedAt: string;
  expiresAt: string;
}

export class VersionConflictError extends Error {
  constructor(sessionId: string, expectedVersion: number) {
    super(`Optimistic lock conflict on session ${sessionId} (expected version ${expectedVersion})`);
    this.name = "VersionConflictError";
  }
}

/**
 * Production systems back this interface with PostgreSQL (JSONB + row-level
 * security + version CAS) and a Redis hot-cache (key: `orderops:session:{tenantId}:{sessionId}`).
 */
export class InMemorySessionStore {
  private readonly store = new Map<string, Map<string, AgentSessionState>>();
  private readonly nowFn: () => number;

  constructor(nowFn: () => number = () => Date.now()) {
    this.nowFn = nowFn;
  }

  save(state: AgentSessionState, expectedVersion?: number): AgentSessionState {
    let tenantMap = this.store.get(state.tenantId);
    if (!tenantMap) {
      tenantMap = new Map<string, AgentSessionState>();
      this.store.set(state.tenantId, tenantMap);
    }

    const existing = tenantMap.get(state.sessionId);
    if (expectedVersion !== undefined) {
      if (!existing || existing.version !== expectedVersion) {
        throw new VersionConflictError(state.sessionId, expectedVersion);
      }
    }

    const nextState: AgentSessionState = {
      ...structuredClone(state),
      version: existing ? existing.version + 1 : state.version,
      updatedAt: new Date(this.nowFn()).toISOString(),
    };
    tenantMap.set(state.sessionId, nextState);
    return structuredClone(nextState);
  }

  load(tenantId: string, sessionId: string): AgentSessionState | null {
    const state = this.store.get(tenantId)?.get(sessionId);
    if (!state) return null;
    if (this.nowFn() > Date.parse(state.expiresAt)) {
      return { ...structuredClone(state), status: "expired" };
    }
    return structuredClone(state);
  }
}

export interface KnowledgeChunk {
  docId: string;
  clauseId: string;
  tenantId: string; // "global" or specific tenantId
  aclRoles: string[];
  title: string;
  content: string;
  terms: string[];
  /** Simulated dense embedding vector (4-dim: [delay/sla, refund/cost, supplier, eu-rebate]) */
  embedding: [number, number, number, number];
}

export interface SearchResult {
  chunk: KnowledgeChunk;
  bm25Score: number;
  vectorScore: number;
  rrfScore: number;
}

const CORPUS: KnowledgeChunk[] = [
  {
    docId: "POL-RET-APAC",
    clauseId: "4.2",
    tenantId: "tenant-apac-01",
    aclRoles: ["ops_agent", "supervisor"],
    title: "APAC Delayed Shipment Compensation",
    content: "If carrier delay exceeds 72 hours past promisedDeliveryDate, approve up to $250 USD goodwill refund without HITL.",
    terms: ["delay", "carrier", "72", "hours", "refund", "250", "apac", "goodwill"],
    embedding: [0.85, 0.90, 0.10, 0.05],
  },
  {
    docId: "POL-SUP-SLA",
    clauseId: "2.1",
    tenantId: "global",
    aclRoles: ["ops_agent", "supervisor"],
    title: "Global Supplier Escalation SLA",
    content: "When waiting for supplier confirmation, pause session state for up to 24 hours before escalating to supervisor.",
    terms: ["supplier", "pause", "session", "24", "hours", "escalate", "sla"],
    embedding: [0.55, 0.10, 0.95, 0.05],
  },
  {
    docId: "POL-VIP-EU",
    clauseId: "9.1",
    tenantId: "tenant-eu-02",
    aclRoles: ["supervisor"],
    title: "EU-02 Confidential Margin Rebate",
    content: "Confidential EU-02 wholesale rebate is 18% on SKU-PRO-900.",
    terms: ["eu-02", "rebate", "18%", "confidential", "sku-pro-900", "refund"],
    embedding: [0.05, 0.40, 0.05, 0.95],
  },
];

function cosineSimilarity(a: number[], b: number[]): number {
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  const denom = Math.sqrt(normA) * Math.sqrt(normB);
  return denom === 0 ? 0 : dot / denom;
}

function embedQuery(queryTerms: string[]): [number, number, number, number] {
  const has = (words: string[]) => (words.some((w) => queryTerms.includes(w)) ? 1 : 0);
  return [
    has(["delay", "carrier", "72", "hours", "sla"]) * 0.9,
    has(["refund", "250", "goodwill", "rebate"]) * 0.9,
    has(["supplier", "pause", "escalate"]) * 0.9,
    has(["eu-02", "rebate", "wholesale"]) * 0.9,
  ];
}

export class MultiTenantKnowledgeBase {
  /**
   * Hybrid Search (BM25 + Vector Cosine) with mandatory ACL pre-filtering.
   * Never filter after LLM generation.
   */
  hybridSearch(params: {
    query: string;
    tenantId: string;
    callerRoles: string[];
    topK?: number;
  }): SearchResult[] {
    const topK = Math.min(20, Math.max(1, Math.floor(params.topK ?? 3)));
    const queryTerms = params.query
      .toLowerCase()
      .split(/[^\p{L}\p{N}-]+/u)
      .filter((t) => t.length > 1);

    if (queryTerms.length === 0) return [];

    // 1. Mandatory Pre-filter: tenant isolation + ACL role intersection
    const authorized = CORPUS.filter(
      (c) =>
        (c.tenantId === params.tenantId || c.tenantId === "global") &&
        c.aclRoles.some((r) => params.callerRoles.includes(r)),
    );
    if (authorized.length === 0) return [];

    // 2. BM25 (k1 = 1.2, b = 0.75) and Vector Cosine Similarity
    const k1 = 1.2;
    const b = 0.75;
    const avgDocLen = authorized.reduce((acc, c) => acc + c.terms.length, 0) / authorized.length;
    const qVec = embedQuery(queryTerms);

    const scored = authorized.map((chunk) => {
      let bm25Score = 0;
      const docLen = chunk.terms.length;
      for (const term of new Set(queryTerms)) {
        const tf = chunk.terms.filter((t) => t === term).length;
        if (tf === 0) continue;
        const df = authorized.filter((c) => c.terms.includes(term)).length;
        const idf = Math.log(1 + (authorized.length - df + 0.5) / (df + 0.5));
        const tfNorm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (docLen / avgDocLen)));
        bm25Score += idf * tfNorm;
      }
      const vectorScore = cosineSimilarity(qVec, chunk.embedding);
      return { chunk, bm25Score, vectorScore };
    });

    // 3. Reciprocal Rank Fusion (RRF, k = 60); only positive-score candidates contribute
    const chunkKey = (c: KnowledgeChunk) => `${c.docId}#${c.clauseId}`;
    const byBm25 = scored.filter((s) => s.bm25Score > 0).sort((a, b) => b.bm25Score - a.bm25Score);
    const byVec = scored.filter((s) => s.vectorScore > 0).sort((a, b) => b.vectorScore - a.vectorScore);
    const rrfK = 60;

    return scored
      .map((item) => {
        const idx1 = byBm25.findIndex((x) => chunkKey(x.chunk) === chunkKey(item.chunk));
        const idx2 = byVec.findIndex((x) => chunkKey(x.chunk) === chunkKey(item.chunk));
        const rrfScore =
          (idx1 >= 0 ? 1 / (rrfK + idx1 + 1) : 0) + (idx2 >= 0 ? 1 / (rrfK + idx2 + 1) : 0);
        return { ...item, rrfScore };
      })
      .filter((item) => item.rrfScore > 0)
      .sort((a, b) => b.rrfScore - a.rrfScore || chunkKey(a.chunk).localeCompare(chunkKey(b.chunk)))
      .slice(0, topK);
  }
}

export function verifyCitations(
  answerText: string,
  retrieved: SearchResult[],
  requireCitation = true,
): { valid: boolean; cited: string[]; fabricated: string[]; missingCitation: boolean } {
  const allowed = new Set(retrieved.map((r) => `${r.chunk.docId}#${r.chunk.clauseId}`));
  const matches = [...answerText.matchAll(/\[([A-Za-z0-9-]+#[0-9.]+)\]/g)].map((m) => m[1]);
  const fabricated = matches.filter((id) => !allowed.has(id));
  const missingCitation = requireCitation && matches.length === 0;
  return {
    valid: !missingCitation && fabricated.length === 0,
    cited: matches,
    fabricated,
    missingCitation,
  };
}

function main(): void {
  let fakeNow = Date.parse("2026-11-21T10:00:00Z");
  const sessions = new InMemorySessionStore(() => fakeNow);
  const kb = new MultiTenantKnowledgeBase();

  // Step 1: Start session and pause while waiting for supplier reply
  const initialState: AgentSessionState = {
    sessionId: "sess-88412",
    tenantId: "tenant-apac-01",
    ticketId: "TKT-88412",
    status: "waiting_external",
    turnCount: 2,
    version: 1,
    waitingFor: "supplier_eta_webhook",
    messages: [
      { role: "user", content: "Order ORD-2026-88412 is delayed > 72h. Check policy.", createdAt: "2026-11-21T10:00:00Z" },
    ],
    updatedAt: new Date(fakeNow).toISOString(),
    expiresAt: new Date(fakeNow + 24 * 3600 * 1000).toISOString(),
  };
  sessions.save(initialState);

  // Step 2: Resume hours later with optimistic lock CAS and persist updated state
  fakeNow += 4 * 3600 * 1000;
  const loaded = sessions.load("tenant-apac-01", "sess-88412");
  if (!loaded || loaded.status === "expired") {
    throw new Error("Session missing or expired");
  }
  const updated = sessions.save(
    {
      ...loaded,
      status: "active",
      turnCount: loaded.turnCount + 1,
      waitingFor: undefined,
    },
    loaded.version,
  );
  const reloaded = sessions.load("tenant-apac-01", "sess-88412");

  // Demonstrate concurrent wake-up conflict
  let conflictCaught = false;
  try {
    sessions.save({ ...loaded, status: "active" }, loaded.version);
  } catch (err) {
    conflictCaught = err instanceof VersionConflictError;
  }

  // Step 3: Agentic RAG with strict tenant pre-filtering
  const results = kb.hybridSearch({
    query: "carrier delay 72 hours refund policy",
    tenantId: reloaded!.tenantId,
    callerRoles: ["ops_agent"],
    topK: 3,
  });

  console.log("Resumed session:", reloaded?.sessionId, "turn:", reloaded?.turnCount, "version:", updated.version, "conflictCaught:", conflictCaught);
  console.log(
    "Authorized chunks:",
    results.map((r) => `${r.chunk.docId}#${r.chunk.clauseId} (tenant=${r.chunk.tenantId})`),
  );

  // Step 4: Citation verification
  const goodAnswer = "Per [POL-RET-APAC#4.2], approve up to $250 USD goodwill refund without HITL.";
  const badAnswer = "Per [POL-VIP-EU#9.1], apply 18% wholesale rebate.";
  const uncitedAnswer = "Approve up to $250 USD goodwill refund without HITL.";
  console.log("Good citation check:", verifyCitations(goodAnswer, results));
  console.log("Bad citation check:", verifyCitations(badAnswer, results));
  console.log("Uncited check:", verifyCitations(uncitedAnswer, results));

  // Step 5: Cost check for Agentic RAG turn (+1,800 input tokens, +350 output tokens on Sonnet 5.5)
  const chunkInputOnlyCost = calculateCostUsd("claude-sonnet-5-5", {
    input_tokens: 1800,
    output_tokens: 0,
  });
  const ragTurnCost = calculateCostUsd("claude-sonnet-5-5", {
    input_tokens: 1800,
    output_tokens: 350,
  });
  console.log("Retrieved chunks input cost (USD):", chunkInputOnlyCost.toFixed(6));
  console.log("Single Agentic RAG turn cost incl. 350 output tokens (USD):", ragTurnCost.toFixed(6));
}

main();
