# Fact Baseline — Claude API & Enterprise Agent Ecosystem (2026-11)

Verified on **2026-11-21** via web search against official Anthropic documentation, package registries, and MCP specification sources. Items marked `⚠️` are time-sensitive (prices, SDK versions, model IDs, or fast-moving specs) and must be re-checked during future scans.

## 1. Claude API Models & List Pricing (`⚠️` volatile)

Standard global routing list prices (per 1M tokens = `MTok`):

| Model Tier | Model ID (canonical) | Input ($/MTok) | Output ($/MTok) | Prompt Cache Write (5m / 1h) | Prompt Cache Read | Notes |
|---|---|---|---|---|---|---|
| High-end Reasoning | `claude-opus-5-5` | $4.00 | $20.00 | 1.25× ($5.00) / 2.0× ($8.00) | 0.05× ($0.20) | Flagship agentic coding & complex reasoning |
| Balanced Default | `claude-sonnet-5-5` | $2.00 | $10.00 | 1.25× ($2.50) / 2.0× ($4.00) | 0.05× ($0.10) | Primary production workhorse |
| Fast / Routing (≤100K) | `claude-haiku-5-5` | $0.10 | $0.50 | 1.25× ($0.125) / 2.0× ($0.20) | 0.10× ($0.01) | High-volume classification, routing, guardrails |
| Fast / Routing (>100K) | `claude-haiku-5-5` | $0.50 | $2.50 | 1.25× ($0.625) / 2.0× ($1.00) | 0.10× ($0.05) | Higher tier applies to whole request when prompt+cache >100K tokens |

- Output tokens consistently cost **5×** base input across active Claude 5.5 tiers.
- **Batch API**: **50% discount** on both input and output tokens across all tiers (e.g., `claude-sonnet-5-5` drops to $1.00 input / $5.00 output per MTok) for asynchronous workloads.
- **Data Residency (`inference_geo: "us"`)**: **1.1× multiplier** across all token categories (input, output, cache writes, cache reads).
- **Context Window**: Up to **1M tokens** on flagship/enterprise tiers (exact availability varies by model tier and org plan `⚠️`).

## 2. Prompt Caching Mechanics (`⚠️` volatile)

- Controlled via `cache_control: { "type": "ephemeral" }` (default 5-minute TTL) or `{ "type": "ephemeral", "ttl": "1h" }`.
- **Minimum cacheable prefix thresholds** (silent no-op if below threshold — returns `0` cache_creation_input_tokens without error):
  - 512 tokens on newer Claude 5 / 5.5 flagship models (`claude-opus-5-5`);
  - 1,024 tokens on standard Sonnet tiers (`claude-sonnet-5` / prior Sonnet 4.5/4.6);
  - 4,096 tokens on older Haiku 4.5 / Opus 4.5/4.6 (`⚠️` verify per-model threshold in docs before deployment).
- **Break-even math**:
  - 5m TTL write surcharge = `+0.25×` base input; each read saves `0.90×` (at 0.1× read) or `0.95×` (at 0.05× read) → breaks even after **1 cache read**.
  - 1h TTL write surcharge = `+1.00×` base input; each read saves `0.90×`–`0.95×` → breaks even after **2 cache reads**.
- Prefix matching is exact from the start of the request (`tools` → `system` → `messages`): any mutation in an earlier block invalidates all downstream cache breakpoints.

## 3. Tool Use, Structured Outputs & Extended Thinking

- **Structured JSON Outputs**: `output_config.format` accepts a JSON Schema (wrapped ergonomically via Zod in TS or Pydantic in Python) to enforce schema-compliant final text output without prefill hacks.
- **Strict Tool Use**: Setting `strict: true` on tool definitions enforces schema-compliant tool names and input payloads at decoding time.
- **Extended Thinking**: Enabled via `thinking: { type: "enabled", budget_tokens: N }` (or adaptive reasoning modes on newer models). Thinking blocks are returned transparently as `thinking` content blocks; `max_tokens` must exceed `budget_tokens` to leave room for the final answer/tool calls. In multi-turn tool loops, prior assistant `thinking` blocks (with their signatures) must be preserved when passing assistant turns back to the API.

## 4. Official SDKs (`⚠️` volatile)

- **TypeScript SDK**: `@anthropic-ai/sdk` — latest stable `v1.10.0` (2026-11).
- **Python SDK**: `anthropic` — latest stable `v2.11.0`, requires Python 3.10+ (2026-11).
- **Claude Agent SDK** (formerly Claude Code SDK): `@anthropic-ai/claude-agent-sdk` (TS) and `claude-agent-sdk` (Python) — embeds Claude Code's agent loop, context compaction, MCP integration, hooks, and permission controls (`allowedTools`, `disallowedTools`).

## 5. Model Context Protocol (MCP) (`⚠️` volatile)

- **Transport**: **Streamable HTTP** has superseded legacy HTTP+SSE for remote/enterprise MCP servers, unifying JSON-RPC POST and optional streaming responses on a single HTTP endpoint behind standard API gateways and load balancers. `stdio` remains for local subprocess tools.
- **Stateless Scaling**: MCP 2026 spec revisions strengthen **Stateless HTTP** (`stateless_http=True`, `json_response=True`) for horizontal scaling behind load balancers without sticky sessions.
- **Claude API MCP Connector**: Messages API accepts `mcp_servers` (remote Streamable HTTP + OAuth 2.1 / Bearer auth) and `tools: [{ type: "mcp_toolset", mcp_server_name: "..." }]`, allowing Claude API to invoke remote MCP tools directly without a custom client loop (remote HTTP only; no local stdio).

## 6. Sources

- Anthropic Claude API pricing & prompt caching docs (`claude.com/pricing`, `docs.anthropic.com` — checked 2026-11-21).
- Anthropic Structured Outputs, Tool Use, Extended Thinking & MCP Connector docs (`claude.com`, `anthropic.com` — checked 2026-11-21).
- npm (`@anthropic-ai/sdk`), PyPI (`anthropic`), and MCP specification (`modelcontextprotocol.io` — checked 2026-11-21).
