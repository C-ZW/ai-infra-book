# omp CLI — NVIDIA Models Reference

**Tool:** `omp` v16.2.2 at `~/.bun/bin/omp`  
**Provider:** NVIDIA NIM  
**Rate limit:** 25 requests/minute  
**Tested:** 2026-06-28 · **Re-tested:** 2026-07-01 (see availability notes below)

## Usage

```bash
# Non-interactive single prompt (print mode)
omp -p --model="nvidia/<org>/<model-name>" "your prompt here"

# Pipe file contents
omp -p --model="nvidia/deepseek-ai/deepseek-v4-flash" "$(cat file.md)"

# With thinking level suffix (colon notation)
omp -p --model="nvidia/deepseek-ai/deepseek-v4-flash:xhigh" "your prompt"
# levels: minimal, low, medium, high, xhigh, auto

# Redirect output to file
omp -p --model="nvidia/qwen/qwen3-235b-a22b" "prompt" > output.md 2>&1
```

## Confirmed Available Models

| Model | ID | Size / Notes |
|---|---|---|
| DeepSeek V4 Flash | `nvidia/deepseek-ai/deepseek-v4-flash` | Fast, default in config |
| DeepSeek V4 Pro | `nvidia/deepseek-ai/deepseek-v4-pro` | Stronger DeepSeek V4 |
| Qwen3 Coder 480B | `nvidia/qwen/qwen3-coder-480b-a35b-instruct` | 480B MoE, coding focus |
| Qwen3.5 397B A17B | `nvidia/qwen/qwen3.5-397b-a17b` | 397B MoE ✅ re-confirmed 2026-07-01 |
| Qwen3.5 122B A10B | `nvidia/qwen/qwen3.5-122b-a10b` | 122B MoE ✅ confirmed 2026-07-01 (fast, good reasoning) |
| Qwen3-Next 80B | `nvidia/qwen/qwen3-next-80b-a3b-instruct` | 80B, next-gen Qwen |
| Qwen2.5 Coder 32B | `nvidia/qwen/qwen2.5-coder-32b-instruct` | 32B, coding focus |
| GPT-OSS 120B | `nvidia/openai/gpt-oss-120b` | OpenAI family, 120B |
| GPT-OSS 20B | `nvidia/openai/gpt-oss-20b` | OpenAI family, 20B |
| Llama 3.3 70B | `nvidia/meta/llama-3.3-70b-instruct` | Meta, solid general |
| Llama 4 Maverick 17B | `nvidia/meta/llama-4-maverick-17b-128e-instruct` | 128-expert MoE |
| GLM-5.1 | `nvidia/z-ai/glm-5.1` | Zhipu AI |
| Step 3.5 Flash | `nvidia/stepfun-ai/step-3.5-flash` | StepFun, fast |
| Step 3.7 Flash | `nvidia/stepfun-ai/step-3.7-flash` | StepFun, latest |
| Gemma 4 31B | `nvidia/google/gemma-4-31b-it` | Google Gemma |
| Phi-4 Mini | `nvidia/microsoft/phi-4-mini-instruct` | Microsoft, small |

## Not Available (404)

| Model | ID |
|---|---|
| DeepSeek R1-0528 | `nvidia/deepseek-ai/deepseek-r1-0528` |
| DeepSeek V3.1 | `nvidia/deepseek-ai/deepseek-v3.1` |
| DeepSeek V3.2 | `nvidia/deepseek-ai/deepseek-v3.2` |
| Llama 3.1 405B | `nvidia/meta/llama-3.1-405b-instruct` |
| Llama 4 Scout 17B | `nvidia/meta/llama-4-scout-17b-16e-instruct` |
| Qwen3 235B A22B | `nvidia/qwen/qwen3-235b-a22b` | ⚠️ was available 2026-06-28, now **404 (2026-07-01)** |

## Availability re-test — 2026-07-01

Confirmed **working** today (used as paradox-book review panel): `deepseek-v4-flash`,
`deepseek-v4-pro`, `openai/gpt-oss-120b`, `meta/llama-3.3-70b-instruct`,
`qwen/qwen3.5-397b-a17b`, `qwen/qwen3.5-122b-a10b`, `z-ai/glm-5.1`.
Newly **404**: `qwen/qwen3-235b-a22b` (lineup drifted since 2026-06-28 — always probe before a batch run).

## Recommended for skill/doc review tasks

Best balance of capability and speed for reviewing technical specifications:

1. `nvidia/deepseek-ai/deepseek-v4-pro` — strongest DeepSeek, good analytical depth
2. `nvidia/qwen/qwen3-235b-a22b` — large MoE, excellent at structured analysis
3. `nvidia/openai/gpt-oss-120b` — different architecture, independent perspective
4. `nvidia/meta/llama-3.3-70b-instruct` — reliable, fast, good instruction following

For cost-sensitive batch work: `nvidia/deepseek-ai/deepseek-v4-flash` (fast + cheap).
For coding-heavy review: `nvidia/qwen/qwen3-coder-480b-a35b-instruct`.
