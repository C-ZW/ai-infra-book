---
last_verified: 2026-06-13
review_after_days: 90
status: research-agent-draft
source: web research 2026-06-13
topic: "Why eight AI labs' LLMs have different strengths — fact baseline"
---

# AI-Lab Landscape Fact Baseline (landscape-2026-06)

This file is the single source of truth for the book *Why do different labs' LLMs have different strengths?*
Chapter authors: do NOT pull versions, prices, GPU counts, or rankings from memory. Pull them from here,
and copy the date stamp with them. This is the most time-sensitive topic in the whole shelf — anything
here is a snapshot of **2026-06-13** and will rot within months.

## How to read the confidence markers

| Marker | Meaning | How to write it |
|---|---|---|
| ✅ | **Confirmed** — primary source (lab blog, arXiv paper, Wikipedia with citation) or multiple independent secondaries agree. | State as fact, but keep the date stamp. |
| 🟡 reputation | **Reputation / consensus** — widely believed, hard to A/B prove, shifts over time (e.g. "Claude is best at coding"). | Write as "is known for / associated with", never "is the best at". |
| ⚠️ | **Unconfirmed / contested / single-source / fast-moving** — a number that's disputed, a claim from a secondary aggregator I could not trace to a primary, or a forward-looking announcement not yet shipped. | Hedge explicitly. Name the dispute. Do not assert as timeless fact. |

**Golden rule for the whole book:** there is NO single uniform winner, rankings change monthly, and benchmarks
get contaminated. Every "X is strongest at Y" must be framed as "as of 2026-06, X is reputed to lead at Y."
This caveat is the spine of the benchmarks chapter and should echo through every lab chapter.

**Sourcing note:** much of the *very latest* 2026 version/price detail (GPT-5.5, Gemini 3.5, Fable 5, Muse Spark,
DeepSeek V4, Qwen3.6) comes from secondary aggregators and tech-press, not yet from durable primary docs at
research time. Those are marked 🟡 or ⚠️ accordingly. The *durable structural facts* (architecture, scaling laws,
alignment-method attributions, the 2024–2025 reasoning shift, training-cost disputes) are anchored to primary
sources (arXiv, lab blogs, Wikipedia) and are the safest material to build chapters on.

---

# PART 1 — THE EIGHT LABS

Each lab: current models (date-stamped) → known strengths (reputation) → product/strategy → compute/infra →
signature techniques → **one-line "signature strength & the WHY"** synthesis (the spine).

---

## 1. OpenAI

### Models (as of 2026-06)
- ✅ **GPT-5** launched 2025 as the unifying family; by **2026-02-13** OpenAI consolidated everything into the GPT-5 line and **retired** the older GPT-4 family AND the standalone o-series reasoning models (o1, o3, o4-mini). [aicomparison, ai-toolbox]
- 🟡 **GPT-5.5** is described as the current flagship for complex reasoning/coding, **released 2026-04-24**; "Instant" default variant rolled out ~2026-05-05. Reasoning-effort levels: none / low / medium(default) / high / xhigh; smaller variants GPT-5.x mini and nano for cheap/low-latency work. [TechCrunch, Vellum, aicomparison] ⚠️ exact sub-version naming (5.3 Instant / 5.4 Thinking / 5.4 Pro / 5.5 / 5.6) is messy across aggregators — treat the **GPT-5 family + unified router + reasoning-effort dial** as the durable fact, individual point-versions as fast-moving.
- ✅ Key structural shift: OpenAI **merged "reasoning" and "general" into one model with a router** that auto-escalates to deeper thinking ("Instant" vs "Thinking"). This is itself a notable 2026 architecture-of-product decision.

### Known strengths (🟡 reputation)
- Agentic coding, computer-use, "give it a messy multi-part task and let it plan/use tools/check its work", knowledge work, early scientific research. [OpenAI GPT-5.5 page via secondaries]
- Strong math reasoning (claimed top-tier AIME). Broad general capability + the largest consumer mindshare.

### Product / strategy
- ✅ **ChatGPT is the scale leader**: ~900M weekly active users (announced 2026-02, up from ~800M Oct 2025, ~400M Feb 2025); crossed **1B monthly active app users** by ~May 2026 — fastest app ever to the milestone. ~50M paying subscribers + >9M paying business users. [demandsage, TechnologyChecker]
- Two-sided: consumer ChatGPT + developer API/platform.

### Compute / infra
- ✅ Historically Microsoft-Azure-dependent (Azure was exclusive cloud). 2025–2026 the relationship loosened: OpenAI committed to buy an **incremental ~$250B in Azure** services but is explicitly building **compute independence**. [OpenAI/Microsoft joint statement]
- ✅ **Stargate**: announced 2025-01, $100B initial → **$500B over 4 years**, backers OpenAI + SoftBank + Oracle + MGX (Abu Dhabi). Target 10GW US compute by 2029; OpenAI said (2026-04) it had **already surpassed that milestone**, +3GW in 90 days. [DCD, OpenAI]
- ⚠️ **Setbacks (2026)**: Microsoft *took over* a second Stargate site (Narvik, Norway, ~30k Nvidia chips); OpenAI *halted* its UK Stargate over energy cost/regulation. Stargate is real and huge but not friction-free — write it as "ambitious + contested," not "smooth."

### Signature techniques
- RLHF at scale (InstructGPT lineage, see Part 2), then the **reasoning-model paradigm** (o1, Sep 2024) — RL on chains of thought + test-time compute. OpenAI *started* the reasoning-model era.

### ✏️ Signature strength & the WHY
**OpenAI: broadest general capability + consumer dominance + it kicked off the reasoning era. WHY = first-mover
on RLHF-chat (ChatGPT) and on RL-reasoning (o1), the deepest Azure compute relationship, and the largest user
base feeding product iteration.**

---

## 2. Google DeepMind

### Models (as of 2026-06)
- ✅ **Gemini 3** released **2025-11-18** (Gemini 3 Pro + Gemini 3 Deep Think). [Wikipedia: Gemini 3]
- ✅ **Gemini 3.1 Pro** released **2026-02-19**; cited ~77.1% on ARC-AGI-2 (≈2× prior reasoning). [DataCamp, Medium]
- 🟡/⚠️ **Gemini 3.5 Pro** unveiled at Google I/O **2026-05-19**, GA targeted **June 2026**; targets a **2-million-token context window** + "Deep Think" reasoning. ⚠️ As of 2026-06-09 not yet GA / no published independent benchmarks. Treat 2M context as the *headline ambition*, confirmed-shipping only for older 1.5 Pro / coming for 3.5.
- ✅ Long-context heritage is real: **Gemini 1.5 Pro already shipped a 2M-token window** via API (2024). Long context is a genuine, durable Google signature.

### Known strengths (🟡 reputation)
- **Very long context** + **native multimodality** (text/image/audio/video in one model) + strong reasoning ("Deep Think"). Multimodal-native, not bolted-on.

### Product / strategy
- ✅ Deepest product surface of any lab: Search (AI Overviews / AI Mode), Workspace (Gmail/Docs), Android, the Gemini app (~750M MAU per Google; analysts predict 1B by Q3 2026 ⚠️ forecast). The need to serve *Search-scale* traffic shapes their efficiency obsession.

### Compute / infra — the TPU vertical-integration advantage
- ✅ **Self-owned silicon (TPU)** is Google's structural moat. **Ironwood = TPU v7** (GA ~Nov 2025), a pod scales to 9,216 liquid-cooled chips ≈ 42.5 ExaFLOPS, 192GB HBM/chip; ~5× compute vs prior Trillium. Powers Gemini inference at scale. [blog.google, SemiAnalysis]
- ⚠️ **TPU 8 (8t train / 8i inference)** announced at Cloud Next 2026 — forward-looking.
- ✅ Vertical integration: DeepMind co-designs models *with* TPU engineers; cited all-in TCO ~44% lower per Ironwood chip vs a GB200 server (⚠️ vendor-flavored figure). ⚠️ "Google has 10M TPUs" is a widely repeated aggregate — order-of-magnitude, not audited.

### Research depth / heritage
- ✅ DeepMind heritage: **AlphaGo** (beat Lee Sedol, 2016), **AlphaFold** (protein structure; AlphaFold2 2020, Hassabis & Jumper shared **2024 Nobel Prize in Chemistry**). This RL + scientific-discovery DNA is a real differentiator vs labs born purely from LLM scaling.

### ✏️ Signature strength & the WHY
**Google DeepMind: long context + native multimodal + deep research bench. WHY = TPU vertical integration
(own the silicon → train biggest, serve cheapest), DeepMind's AlphaGo/AlphaFold RL-and-science heritage, and
the obligation to serve Search at planetary scale forcing efficiency.**

---

## 3. Anthropic

> Book note: document factually like the others; do NOT center the narrative on Anthropic.

### Models (as of 2026-06)
- ✅ **Claude Opus 4.8** released **2026-05-28** — top-tier for complex reasoning, long-horizon agentic coding, high-autonomy work. [Wikipedia: Claude]
- ✅ **Claude Sonnet 4.6** released **2026-02-17** — near-Opus on coding with better instruction-following/tool reliability.
- ✅ **Claude Haiku 4.5** released **2025-10-15** — fastest/cheapest tier.
- 🟡 **Claude Fable 5** + **Claude Mythos 5** released **2026-06-09** ("Mythos-class", most capable Anthropic models). Fable 5 = public version with safeguards; Mythos 5 = same model, some safeguards removed, restricted to **Project Glasswing** (cybersecurity pros; later select biology researchers). ⚠️ Fable 5 was **removed from Pro/Max/Team/Enterprise plans on 2026-06-23** (reported as **capacity constraints, not a security incident**) and moved to usage-credits — VERY fresh and likely to change. [Anthropic news, TechCrunch, CNBC]

### Known strengths (🟡 reputation)
- **Coding + agentic tasks** is the standout reputation. **Claude Code** (terminal-delegated coding) and computer-use are flagship surfaces. Reputed strong on long-horizon multi-step autonomy and instruction-following.

### Alignment / safety positioning
- ✅ **Constitutional AI** (Bai et al., **Dec 2022**, "Constitutional AI: Harmlessness from AI Feedback", arXiv:2212.08073) — train against a written "constitution" using **RLAIF** (RL from AI Feedback) instead of relying purely on human labels. The 2026 constitution reportedly grew from ~2,700 words (2023) to ~23,000. [Wikipedia]
- ✅ **Interpretability research** is a genuine Anthropic signature: scaling monosemanticity / sparse autoencoders (Templeton et al. 2024, features from Claude 3 Sonnet), **circuit tracing / cross-layer transcoders + attribution graphs** (introduced ~Mar 2025). [transformer-circuits.pub]
- Safety-forward brand positioning generally.

### Compute / infra — multi-cloud
- ✅ **Multi-cloud frontier lab**: AWS is primary. **Project Rainier** (AWS, Indiana) ≈ 500k Trainium2 chips; Anthropic uses >1M Trainium2 chips; expanded deal = up to **5GW of Trainium** + **$100B AWS** commitment over a decade. [Anthropic+Amazon, Data Center Frontier]
- ✅ ALSO **up to 1M Google TPUs** (Oct 2025 deal), multi-GW by 2026. So Anthropic spans **AWS Trainium + Google TPU** (notably uses *neither* its own silicon *nor* primarily Nvidia for the biggest commitments).

### ✏️ Signature strength & the WHY
**Anthropic: coding/agentic reliability + safety & interpretability depth. WHY = Constitutional AI / RLAIF lets
them scale alignment with less human labeling, an unusually deep interpretability research bench, and a
deliberate multi-cloud (Trainium + TPU) compute base.**

---

## 4. Meta

### The big 2025–2026 story: Meta pivoted AWAY from open-weight at the frontier
- ✅ **Llama 4** "herd" announced **2025-04** — first natively-multimodal, first MoE Llama: **Scout** (17B active, 16 experts, up to 10M-token context) and **Maverick** (17B active, 128 experts). [ai.meta.com]
- ⚠️ **Llama 4 Behemoth (~2T scale)** never publicly shipped — "in training" at launch, then **effectively shelved** (MoE-routing / chunked-attention issues at 2T scale, Meta lost confidence). Treat as "announced, not released."
- ✅ **Muse Spark** (announced **2026-04-08**, about.fb.com / ai.meta.com) — Meta's **first proprietary, closed-weight frontier model**, from the new **Meta Superintelligence Labs (MSL)** under Alexandr Wang. **You cannot download the weights.** It now powers the Meta AI app. This ends Meta's 7-year open-weight-at-the-frontier identity. [CNBC, about.fb.com]

### Open-weight strategy & licensing (the legacy that built the ecosystem)
- ✅ Llama's **open weights** seeded a huge ecosystem (fine-tunes, on-prem, research). But the license was never pure-OSI: **Llama 4 Community License** restricts commercial use above **700M MAU** (must request separate license) and **prohibited EU-domiciled** use/distribution at launch. So "open" always had strings.
- 🟡 WHY the pivot: frontier-training cost (Meta capex cited ⚠️ ~$115–135B in 2026), worry that **Chinese labs build commercial products on Llama**, need to monetize via platform integration + proprietary user data.

### Compute / infra
- ✅ Massive Nvidia H100 fleet (publicly targeted ~350k H100s for Llama-era training ⚠️ 2024-era figure). Among the largest GPU buyers. Huge 2026 capex.

### ✏️ Signature strength & the WHY
**Meta: built the open-weight ecosystem (Llama), now pivoting to proprietary at the frontier (Muse Spark).
WHY = open weights gave reach + goodwill + a research flywheel, but rising frontier costs, fear of rivals
free-riding, and the pull of monetizing via 3B-user platforms (FB/IG/WhatsApp) flipped the strategy in 2026.**
⚠️ This is the single most "fresh and surprising" lab story — flag it as a *2026 inflection*, not settled history.

---

## 5. Mistral AI

### Models (as of 2026-06)
- ✅/🟡 **Mistral Large 3** (Dec 2025) — flagship **open-weight sparse MoE**, ~**675B total / ~41B active**, **256K context**, **Apache 2.0**. Runs at ~41B-dense cost while accessing 675B capacity. [dev.to, IntuitionLabs]
- 🟡 **Mistral Small 4** (2026-03-16) — unifies former Magistral(reasoning)/Pixtral(vision)/Devstral(coding) into one. [Serenities]
- 🟡 **Mistral Forge** (announced GTC Mar 2026) — platform for enterprises to train frontier-grade models on their own data.

### Known strengths (🟡 reputation)
- **Efficiency / strong-small-models** + genuinely **open-weight MoE** (Apache 2.0 is more permissive than Llama's license). The European/sovereignty angle is core to the brand.

### Sovereignty angle & partnerships
- ✅ Europe's flagship frontier lab; "sovereign AI" positioning. Raised **$830M** (per reports) to build a sovereign data center near Paris (~13,800 Nvidia GB300 GPUs, ~Q2 2026). Nvidia partnership (~18,000 Grace Blackwell in France). Partnerships incl. **SAP** (German/EU sovereign stack), **Dassault Systèmes**, and an MGX+Nvidia 1.4-GW France campus (later-2020s, ⚠️ forward-looking). [actuia, NVIDIA newsroom, businesswire]

### ✏️ Signature strength & the WHY
**Mistral: efficient, truly-open (Apache-2.0) MoE + European sovereignty. WHY = a small team competing on
efficiency not raw scale, Apache-2.0 openness as differentiation vs Llama's restricted license, and EU
demand for a non-US-dependent "sovereign" AI stack (govt/enterprise/regulated-industry partnerships).**

---

## 6. xAI

### Models (as of 2026-06)
- 🟡/⚠️ **Grok 5** — Musk announced Q1-2026 target, **reported ~6T parameters** (MoE) — claimed "largest publicly announced model ever," trained on Colossus 2. ⚠️ Parameter count and exact ship status are Musk/press claims; verify before stating as fact. **UPDATE (ch10 + fact-check, 2026-06-13): the Q1-2026 window slipped to ~Q2-2026 and Grok 5 had NOT publicly shipped as of 2026-06-13** — treat "released" as unconfirmed; ch10 already hedges this in prose. Recheck ship status + the 6T-param claim on next scan.
- (Grok 4-era was the prior public flagship; Grok ships fast and iterates publicly.)

### The signature asset: Colossus
- 🟡/⚠️ **Colossus** supercluster (Memphis). Reported (2026-01-15) **~555,000 GPUs**: Colossus 1 ~230k operational (incl. ~30k GB200s); Colossus 2 first batch ~550k GB200/GB300 coming online; ~**2 GW** total power. [Introl, Musk on X, NVIDIA newsroom] ⚠️ These are Musk/press figures, fast-moving — give the number AND "self-reported, rapidly changing."
- ✅ Speed-to-scale is the real story: xAI went from nothing to a top-tier cluster astonishingly fast (Colossus 1 stood up in ~months in 2024). Musk's stated 5-yr goal: **50M "H100-equivalents"** by ~2030 (⚠️ aspirational). [Tom's Hardware]

### Real-time data from X
- ✅ Grok's structural differentiator: native access to **real-time X (Twitter) data** — freshness/currency other models lack without web tools.

### ✏️ Signature strength & the WHY
**xAI: speed-to-scale + real-time data + raw compute. WHY = owning Colossus (self-built, among the world's
largest GPU clusters) lets them brute-force fast, and privileged live access to the X firehose gives Grok
real-time freshness rivals must bolt on.**

---

## 7. DeepSeek

### Models (as of 2026-06)
- ✅ **DeepSeek-V3** (Dec 2024, arXiv:2412.19437): MoE, **671B total / 37B active**, 256 routed experts, **MLA**, auxiliary-loss-free load balancing, **Multi-Token Prediction**, **FP8** training, 14.8T training tokens.
- ✅ **DeepSeek-R1** (**2025-01-20**): 671B open-weight **reasoning** model — the one that shocked the market.
- 🟡 **DeepSeek-V4** (Pro + Flash) reportedly shipped **2026-04-24**: MoE, ~1M-token context; agentic scores cited alongside GPT-5.5 / Claude Opus 4.7, at radically lower price (75% V4-Pro discount made permanent 2026-05-22). [MindStudio, DataCamp] ⚠️ secondary-sourced, fast-moving.

### Efficiency innovations (the durable, citable core)
- ✅ **MLA (Multi-head Latent Attention)** — introduced in **DeepSeek-V2**, compresses KV into a low-dim latent → big KV-cache / memory savings. A DeepSeek signature.
- ✅ **GRPO (Group Relative Policy Optimization)** — introduced in **DeepSeekMath**, used in V3/R1; memory-efficient RL (drops the critic, scores a *group* of samples relative to each other). Central to R1.
- ✅ MoE + MTP + FP8 + auxiliary-loss-free balancing — a stack of efficiency tricks, not one trick.

### The cost-disruption narrative (handle the numbers carefully)
- ✅ The famous **~$5.6M** figure traces to the **V3 technical report**: ~2.788M H800 GPU-hours for the *final pre-training run*. **Caveat (critical): it is GPU-pre-training compute ONLY** — excludes R&D, salaries, infrastructure, failed runs, prior-model investment.
- ⚠️ Critics put true all-in cost far higher: estimates of **$1.3B / $1.6B** when you include the GPU fleet & R&D. So write: "~$5.6M *for the final training run* — but total program cost is much higher and disputed."
- ✅ Journalists frequently **confused V3's $5.6M with R1**; R1's own training was reported separately (~$294k, 512 H800s ⚠️ also a narrow figure).
- ✅ Market impact: **2025-01-27 Nvidia fell ~17%, ≈$600B market cap wiped** on the R1 efficiency shock. ✅ But it **recovered** within months — the lasting lesson is "algorithmic efficiency matters as much as scale," not "scaling is dead."

### ✏️ Signature strength & the WHY
**DeepSeek: frontier-ish quality at a fraction of the cost, open-weight. WHY = a stack of efficiency inventions
(MLA, GRPO, MoE, MTP, FP8) born of compute scarcity (export-controlled H800s) forced algorithmic cleverness —
turning a constraint into a moat and resetting the industry's cost expectations.**

---

## 8. Alibaba Qwen

### Models (as of 2026-06)
- ✅ **Qwen3** (2025) — hybrid-reasoning, **119 languages**, full size ladder: edge (0.6B, 1.7B) → laptop (4B, 8B) → datacenter (32B, 235B, 480B); MoE incl. **Qwen3-235B-A22B** and **Qwen3-30B-A3B**, **Apache 2.0**. [qwenlm.github.io]
- 🟡 **Qwen3.5** (2026-02-16, incl. a 397B-A17B MoE), **Qwen3.6-Plus** (2026-04-02, Model Studio), **Qwen3.6-35B-A3B** open-weights on HF/ModelScope (2026-04-17, Apache 2.0). ⚠️ point-versions move monthly; the durable facts are **breadth of sizes + open weights + multilingual**.

### Known strengths (🟡 reputation)
- **Open-weight breadth** (more sizes/variants than almost anyone — edge to datacenter), **multilingual** strength (119 languages), and strong **Chinese/Asian-market** fit. Among the **most-downloaded model families on Hugging Face**.

### Product / strategy
- ✅ Backed by Alibaba Cloud; open weights (mostly Apache 2.0) + hosted API (Model Studio). The "we ship a model for every tier" strategy maximizes ecosystem adoption.

### ✏️ Signature strength & the WHY
**Qwen: the broadest open-weight size ladder + multilingual reach. WHY = Alibaba Cloud's commercial incentive
to seed an ecosystem (a model for every device tier), deep Chinese/Asian-language data, and aggressive
open-weight release driving Hugging Face dominance as a distribution strategy.**

---

# PART 2 — CROSS-CUTTING FACT AREAS

---

## A. Architecture commonality — "same blueprint, different raising"

- ✅ **All current frontier LLMs are decoder-only Transformers with self-attention** (autoregressive next-token prediction). This is the book's central premise and it holds: the *blueprint* is shared. The "different strengths" come from data, scale, alignment, and architectural *variants* — not a different base paradigm.

Common variants and which labs are associated with them:

| Variant | What it does | Associated with (examples) |
|---|---|---|
| ✅ **RoPE** (Rotary Position Embedding) | Encodes position by rotating Q/K vectors; enables long context | Near-universal: Llama, Qwen, Mistral, Gemma, etc. |
| ✅ **GQA** (Grouped-Query Attention) | Query heads share KV heads → smaller KV cache, faster inference | Llama, Qwen, Mistral, Gemma, GPT-OSS — *the default* attention efficiency trick |
| ✅ **MLA** (Multi-head Latent Attention) | Compresses KV into low-dim latent → even smaller KV cache | **DeepSeek** (V2 onward) — their signature |
| ✅ **MoE** (Mixture-of-Experts) | Sparse FFN: route each token to a few "expert" subnetworks → huge total params, small active params | DeepSeek, Mistral, Qwen, Llama 4, Grok 5(claimed), most 2025–26 frontier models |
| ✅ **MTP** (Multi-Token Prediction) | Predict several future tokens during training → denser signal | DeepSeek-V3 |

- 🟡 Takeaway for the book: a 2026 frontier model ≈ decoder-only Transformer + RoPE + (GQA or MLA) + (usually) MoE.
  The *attention efficiency choice* (GQA vs MLA) and *sparsity* (MoE) are where labs differentiate at the architecture level.

---

## B. Scaling laws

- ✅ **Kaplan et al. 2020** ("Scaling Laws for Neural Language Models", OpenAI, **arXiv:2001.08361**, Jan 2020). Loss follows **power laws** in model size N, dataset size D, and compute C (L ∝ N^-α, D^-β, C^-γ), smooth over ~7 orders of magnitude. Conclusion that shaped GPT-3: **make models very large, train on relatively modest data, stop before convergence** (i.e. prioritize parameters over tokens).
- ✅ **Hoffmann et al. 2022 — "Chinchilla"** ("Training Compute-Optimal LLMs", DeepMind, NeurIPS 2022). Trained 400+ models (44M–16B params); found Kaplan **under-weighted data**. For a fixed compute budget, **scale params and tokens TOGETHER (roughly equally)** — double model → double tokens. Their 70B **Chinchilla** trained on **1.4T tokens ≈ 20 tokens/parameter**, and *beat* the much larger Gopher.
- ✅ **The headline number to get right: ~20 tokens per parameter** is the Chinchilla compute-optimal ratio. ⚠️ Note: later replication work (Epoch AI) partially questioned the exact fit, and in practice modern models are trained **far past** 20:1 (e.g. DeepSeek-V3: 671B params on 14.8T tokens) because *inference* cost rewards "overtraining" smaller models. So Chinchilla is the *compute-optimal-for-training* rule, not what labs actually do when serving billions of users.

---

## C. The reasoning-model paradigm (the 2024–2026 shift)

- ✅ **OpenAI o1** released **September 2024** — first mainstream "reasoning model." Trained via **RL to do implicit search via chain-of-thought**; performance scales with **both train-time RL and test-time ("thinking") compute**. Two paradigm shifts: (1) supervised → RL, (2) scaling *inference* compute, not just training. [openai.com/learning-to-reason]
- ✅ **DeepSeek-R1** (2025-01-20) — open-weight reasoning model that showed the recipe could be reproduced cheaply (and largely via RL with verifiable rewards + GRPO). Hugely influential.

Who has reasoning models now (as of 2026-06):
| Lab | Reasoning mode/model | Note |
|---|---|---|
| OpenAI | GPT-5 "Thinking" / reasoning-effort dial | o-series retired, folded into GPT-5 router |
| Google | Gemini "Deep Think" | 3 / 3.1 / 3.5 line |
| Anthropic | Claude extended thinking (Opus/Fable) | reputed agentic/coding strength |
| DeepSeek | R1 → reasoning in V3.1/V4 | open-weight, GRPO-trained |
| Mistral | Magistral (folded into Small 4) | |
| xAI | Grok reasoning modes | |
| Qwen | Qwen3 hybrid reasoning | toggle thinking on/off |
| Meta | Muse Spark (reasoning, closed) | parallel reasoning / "thought compression" claimed ⚠️ |

- 🟡 Takeaway: by 2026 a reasoning mode is **table stakes**, not a differentiator. OpenAI started it (o1); DeepSeek democratized the recipe (R1).

---

## D. Alignment-method evolution (get attributions + dates right)

| Method | Who / paper | Date | One-line |
|---|---|---|---|
| ✅ **RLHF** (at scale) | **InstructGPT**, Ouyang et al. (OpenAI), arXiv:2203.02155 | **Mar 2022** | Train a reward model from human preference rankings, then RL the policy to match. The foundation of ChatGPT-style alignment. |
| ✅ **Constitutional AI / RLAIF** | **Bai et al. (Anthropic)**, arXiv:2212.08073 | **Dec 2022** | Replace much human feedback with **AI feedback** judged against a written "constitution." Anthropic's signature. |
| ✅ **RLVR** (RL from Verifiable Rewards) | multiple (Lambert et al., Guo et al. / DeepSeek-R1, 2024–2025) | 2024–2025 | Drop the learned reward model; use **objective** signals (answer correct? code compiles?). Core to the reasoning era. |
| ✅ **GRPO** (Group Relative Policy Optimization) | **DeepSeek** (DeepSeekMath; used in V3/R1) | 2024 | Critic-free, memory-efficient RL: score a *group* of samples relative to each other. The engine behind R1. |

- 🟡 Narrative arc for the book: **human feedback (2022) → AI feedback / constitution (2022) → verifiable rewards + GRPO (2024–25)**. The trend is **less human labeling, more automatable signal** — which is *why* reasoning models could scale cheaply.

---

## E. Compute & infra — rough order of magnitude (mark uncertain ⚠️)

⚠️ **Every number here is order-of-magnitude and contested.** Use "roughly / reported / self-reported."

| Lab | Compute base | Rough scale (as of 2025–26) | Confidence |
|---|---|---|---|
| OpenAI | Azure + Stargate (own) | Stargate: $500B/4yr, >10GW target (claimed surpassed 2026-04) | ⚠️ headline figures |
| Google | **own TPUs** (Ironwood v7, TPU 8 coming) | "10M TPUs"/">1M H100-equiv" cited; pods of 9,216 chips | ⚠️ aggregate, vendor-flavored |
| Anthropic | **AWS Trainium (primary) + Google TPU** | >1M Trainium2; up to 5GW Trainium + up to 1M TPU deals | ✅ deals announced, ⚠️ live counts |
| Meta | Nvidia H100 fleet | ~350k H100s (2024-era target); ~$115–135B capex 2026 ⚠️ | ⚠️ |
| Mistral | Nvidia (sovereign EU DCs) | ~13,800 GB300 (Paris); ~18,000 Grace Blackwell (France) | 🟡 |
| xAI | **Colossus (own)** | ~555k GPUs reported; ~2GW; goal 50M H100-equiv by ~2030 | ⚠️ Musk/press figures |
| DeepSeek | export-controlled Nvidia (H800) | thousands of H800s (V3: ~2k-GPU-class run) | ⚠️ secretive |
| Qwen/Alibaba | Alibaba Cloud | undisclosed | ⚠️ |

- 🟡 Three "own-silicon-or-self-built-cluster" stories worth highlighting: **Google (TPU)**, **xAI (Colossus)**, and **Anthropic-via-AWS (Trainium)**. Nvidia dependence is the default; escaping it is a strategic theme.

---

## F. Benchmarks & "who is strongest" — the central honest caveat

Major benchmarks/leaderboards in use as of 2026-06:
| Benchmark | Measures | 2026 status |
|---|---|---|
| ✅ **LMArena** (was Chatbot Arena / LMSYS; rebranded "Arena" 2026-01-28) | human-preference Elo, head-to-head votes | most-watched live leaderboard |
| ✅ **MMLU-Pro** | hard multi-choice knowledge (12k Qs, 10 options) | **near-saturated** — top models cluster 88–94%, too tight to separate |
| ✅ **GPQA (Diamond)** | graduate-level science reasoning | **approaching saturation** — frontier models ~94% |
| ✅ **SWE-bench (Verified)** | real GitHub Python issues (500-task human-validated subset) | the key *agentic coding* benchmark |
| ✅ **AIME** | competition math | reasoning models near-perfect |
| 🟡 **Terminal-Bench, ARC-AGI-2** | agentic / abstract reasoning | newer, less saturated |

### 🚨 THE CENTRAL CAVEAT (this is the book's spine — repeat it)
- ✅ **Rankings shift every few months.** A "best model" claim has a shelf life of weeks.
- ✅ **Contamination**: benchmark questions leak into training data → models *recall* instead of *reason*. Inflates scores.
- ✅ **Saturation**: top benchmarks (MMLU-Pro, GPQA) are so crowded at the top they no longer separate frontier models.
- ✅ **No single uniform winner.** Best practice: triangulate three *types* — a static academic eval (MMLU-Pro/GPQA) + a human-preference arena (LMArena) + an agentic suite (SWE-bench/Terminal-Bench). Only agreement across all three is a real signal.
- 🟡 So the book must NEVER say "X is the best model." Say "as of 2026-06, X is reputed to lead at Y, on benchmark Z, which has caveats." Different labs lead on different axes — *that's the whole point of the book.*

---

## G. Data / the "data wall"

- ✅ **Copyright litigation** is live and consequential. **NYT v. OpenAI/Microsoft** (filed Dec 2023): a judge **advanced the core infringement claims** (didn't dismiss); in **Jan 2026** OpenAI was **compelled to produce ~20M anonymized ChatGPT logs** to plaintiffs. ⚠️ No final merits ruling yet as of research time. [Harvard Law Review, Hollywood Reporter, natlawreview] (Many parallel suits from authors, music publishers, etc.)
- ✅ **The data wall**: a widely-cited projection (Epoch AI / "Will we run out of data?") warned the stock of **high-quality public human text could be exhausted ~2026–2028**. The concern is real and roughly *now*.
- 🟡 **Synthetic data** is the main response — but carries **model-collapse** risk (errors compound across generations) especially in hard-to-verify domains (creative writing, hypothesis generation). Verifiable domains (math/code) are safer for synthetic/RL data — which is *why* reasoning models lean on verifiable rewards.
- 🟡 Book framing: the "data wall" + copyright squeeze is a big *reason* labs pivoted toward **RL on verifiable rewards, synthetic data, and proprietary user data** (e.g. Meta's Muse Spark explicitly leans on proprietary user data) rather than just scraping more web text.

---

# PART 3 — FRAGILE FACTS: RECHECK WITHIN 3 MONTHS

Everything below WILL likely be stale by ~2026-09. Re-verify before any chapter ships.

1. ⚠️ **OpenAI flagship version** — GPT-5.5 / 5.6 point-versions and the Instant/Thinking/Pro split. Re-check current top model + naming.
2. ⚠️ **Gemini version** — 3.5 Pro GA status + whether 2M context actually shipped + real benchmarks.
3. ⚠️ **Anthropic Fable 5 / Mythos 5** — *very* fresh (June 2026). Whether Fable 5 returns to subscription plans (was pulled 2026-06-23, "capacity"). Whether "Mythos-class" naming persists.
4. ⚠️ **Meta Muse Spark** — closed-weight pivot just happened (Apr 2026). Confirm it stuck; confirm whether any new open Llama appears. This is the most surprising/volatile lab story.
5. ⚠️ **DeepSeek V4 / R2** — V4 Pro/Flash pricing (the 75% permanent discount) and whether a new R-line reasoning model shipped.
6. ⚠️ **Qwen point-version** — 3.5 / 3.6 / 3.7-Max churn monthly.
7. ⚠️ **Mistral Large 3 / Small 4** — version + the Paris sovereign DC (13,800 GB300) coming-online status.
8. ⚠️ **xAI Grok 5** — ship status + the 6T-param claim + Colossus GPU count (all Musk/press-sourced).
9. ⚠️ **All GPU/TPU counts** in Part 2E — every one is contested/self-reported.
10. ⚠️ **All benchmark numbers/rankings** — saturate and shuffle constantly; never freeze a leaderboard into prose.
11. ⚠️ **NYT v. OpenAI** — watch for a merits ruling / settlement; the discovery order (20M logs) may evolve.
12. ⚠️ **DeepSeek cost figures** — keep the "$5.6M = final-run GPU only; all-in ~$1.3–1.6B; disputed" framing intact; don't let "$5.6M to build a frontier model" sneak in as bare fact.

---

## Master source list (key durable anchors)

**Primary / durable (safest):**
- Kaplan et al. 2020 scaling laws — https://arxiv.org/abs/2001.08361
- Hoffmann et al. 2022 Chinchilla — https://proceedings.neurips.cc/paper_files/paper/2022/file/c1e2faff6f588870935f114ebe04a3e5-Paper-Conference.pdf
- InstructGPT (RLHF), Ouyang et al. 2022 — https://arxiv.org/pdf/2203.02155
- Constitutional AI, Bai et al. 2022 — https://arxiv.org/pdf/2212.08073
- DeepSeek-V3 Technical Report — https://arxiv.org/abs/2412.19437
- OpenAI o1 "Learning to reason with LLMs" — https://openai.com/index/learning-to-reason-with-llms/
- Reasoning model (overview) — https://en.wikipedia.org/wiki/Reasoning_model
- Claude (language model) — https://en.wikipedia.org/wiki/Claude_(language_model)
- Gemini (language model) — https://en.wikipedia.org/wiki/Gemini_(language_model)
- GQA paper — https://arxiv.org/abs/2305.13245
- Anthropic circuit-tracing — https://transformer-circuits.pub/2025/july-update/index.html
- Ironwood TPU — https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/
- Stargate announcement — https://openai.com/index/announcing-the-stargate-project/
- Anthropic+Amazon 5GW compute — https://www.anthropic.com/news/anthropic-amazon-compute
- Meta Muse Spark — https://about.fb.com/news/2026/04/introducing-muse-spark-meta-superintelligence-labs/
- Anthropic Fable 5 / Mythos 5 — https://www.anthropic.com/news/claude-fable-5-mythos-5
- Llama 4 herd — https://ai.meta.com/blog/llama-4-multimodal-intelligence/
- Qwen3 blog — https://qwenlm.github.io/blog/qwen3/
- NYT v OpenAI (HLR) — https://harvardlawreview.org/blog/2024/04/nyt-v-openai-the-timess-about-face/

**Secondary / aggregator (fast-moving, treat as 🟡/⚠️):**
- aicomparison.ai OpenAI 2026 guide; TechCrunch GPT-5.5/Fable5/Muse-Spark coverage; CNBC Meta/OpenAI;
  Introl & SemiAnalysis (TPU/Colossus); MindStudio/DataCamp (DeepSeek V4); Serenities/dev.to (Mistral);
  demandsage/TechnologyChecker (ChatGPT stats); Epoch AI (compute & data-wall); interconnects.ai &
  techstrong.ai (DeepSeek cost dispute); digitalapplied/nanonets (benchmark methodology & contamination).
