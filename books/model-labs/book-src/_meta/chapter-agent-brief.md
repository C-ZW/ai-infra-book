# Chapter-agent shared brief (internal — NOT packaged into the book)

You are writing ONE chapter of a Traditional Chinese (Taiwan) popular-science book:
**《藍圖之外：同一套 Transformer，八家大模型為何各擅勝場》**.
Pure-interest book. Central question: WHY do different AI labs' LLMs have different strengths,
when they all share the same Transformer / self-attention blueprint? Thesis: the architecture (blueprint)
is shared and public; models are **grown, not written**; the differences come from the **five variables**
(資料 / 後訓練·對齊 / 算力·基礎設施 / 研究文化·品味 / 產品取向); and "who is strongest" is unmeasurable /
shifts monthly — only the **style** is stable.

## STEP 1 — read these three files FIRST (they are the contract; obey them exactly)
- `_meta/style-guide.md` — writing contract: reader profile, the EXACT chapter skeleton header names, language rules, depth standards, the five-variable framework.
- `_meta/outline.md` — find YOUR chapter's spec + scope boundaries (what NOT to cover and which chapter owns it), the cross-chapter base table, and the全書 ASCII roadmap.
- `_meta/landscape-2026-06.md` — THE FACT ANCHOR. Pull every version / ranking / price / GPU count / cost / technique-attribution from here, and copy the date stamp + the ✅ / 🟡 / ⚠️ hedging with it. Do NOT use your own memory for any time-sensitive fact.

All paths are relative to: `/Users/cheweichen/Desktop/personal/ai-infra-book/books/model-labs/book-src/`

## Non-negotiable conventions
- **Language**: Traditional Chinese, Taiwan usage. Tech terms keep English (Transformer, attention, pretraining, MoE, RLHF…). **NO simplified-Chinese characters or words** (用「最佳化/記憶體/預設/品質/資訊/程式」). Company & model names in original (OpenAI, Google DeepMind, Anthropic, Meta, Mistral, xAI, DeepSeek, Alibaba/Qwen; GPT, Gemini, Claude, Llama, Grok).
- **Reader = Chewei**, senior backend / distributed-systems engineer, NOT an ML expert. He already read an AI-infra book, so he KNOWS attention / KV-cache / prefill-decode / batching / quantization at the *inference-concept* level — use these as anchors, don't re-teach them. Teach the **training side** (pretraining, scaling laws, post-training/alignment, RL, reward models) from a lower base, with **intuition not math** (no loss functions, no derivations). Bridge new ideas to his REAL systems, naming the specific one the first time: multi-layer cache library (全團隊採用), ECS/NestJS microservices, SQS idempotent consumers, peak RDS CPU −40% (招牌敘事), HPA autoscaling, 自建 FluentBit pipeline, event-driven settlement pipeline.
- **EXACT chapter skeleton** (a consistency scan greps these headers — copy verbatim, in this order):
  1. `# chNN — 章名：副標` then a blockquote line starting `> **本章解決什麼問題**：` (3–5 行：本章在「同一張藍圖、不同養法」地圖的位置、回答哪一格/哪一家的為什麼、與前後章關係). **Part-first chapters (ch01/ch05/ch13/ch20) embed the全書 ASCII roadmap (copy from outline.md) right after the blockquote, marking `◄你在這裡` on this Part's header row.**
  2. `## 從你已知的出發` — bridge from a NAMED real system of his (or from his AI-infra/probability books).
  3. core `##` sections — your content; everything serves the causal "why".
  4. `## 成因拆解` — the book's signature section. MUST contain three parts (a table works well):
     **(a) 五格歸因** over 資料 / 後訓練·對齊 / 算力·基礎設施 / 研究文化·品味 / 產品取向 — mark each ✓主因 / △次因 / (blank), one「為什麼」line each.
     **(b) 影子** — the cost / blind-spot: the same choices that make them strong at X also make them weak/exposed at Y.
     **(c) 何時不成立** — when this "strength" gets overturned (by which task / lab / time), and a reminder it's a 截至 2026-06 snapshot, not a law.
  5. `## 紙上推演` — 2–4 items. Each `### 推演題N` with **[X 分鐘]** + ★~★★★, immediately followed by `#### 推演解答` (full answer + why + common misconception). Types: 口頭重講因果 / 翻譯(把一個模型現象對應回五變數某格) / 反事實 / 找破綻(如「DeepSeek 只花 560 萬美金」) / 對帳(讀者系統的取捨 ↔ 某家的取捨).
  6. `## 自我檢核` — 5–8 口頭自答 questions; prioritize 「為什麼」與「如果不這樣會怎樣」over 「是什麼/哪一版」.
  7. `## 延伸閱讀` — REAL links (prefer ones in landscape's master source list), one line each on why it's worth reading / which part.
- **Facts**: every version / ranking / price / GPU count / cost / attribution comes from landscape, date-stamped 「截至 2026-06」. **NEVER assert an absolute ranking** (「X 是最強的模型」). Write 「截至 2026-06，X 以…著稱／在…benchmark 上領先」+ the benchmark's caveat. For contested numbers (DeepSeek cost, GPU/TPU counts, Colossus size) give BOTH the claimed value AND the caveat/dispute.
- **Web checks**: do 3–8 targeted searches to verify/enrich YOUR chapter's specifics. If web contradicts landscape on a base fact, DO NOT silently change the base — note the conflict in your RETURN summary (the coordinator adjudicates; major corrections need two independent sources). Hedge anything unconfirmed with a date stamp.
- **Depth (this is the「厚實/deep」tier)**: at least one fully-traced causal chain (not「他們資料好」but a specific why-chain, e.g. TPU 垂直整合 → 長上下文成本可控 → Google 長上下文強), and at least one concrete example with a real number (date-stamped). The 影子 is mandatory — never only-upsides.
- **ASCII diagrams**: keep simple. Chinese chars = 2 columns for alignment; AVOID right-border boxes wrapping CJK (alignment is fragile). A `check_diagrams.py` pass verifies later.
- **Write EXACTLY ONE file**: `book-src/chNN-slug.md` (filename given in your brief). Do not touch any other file.
- **Length**: substantial (~2500–4000 Chinese chars of body), but depth over padding.
- **RETURN ONLY a short summary**: sections written, key facts pulled from landscape, web-verifications done, any landscape conflicts found. Your FILE is the real deliverable, not your chat message.
