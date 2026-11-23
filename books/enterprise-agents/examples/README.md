# Enterprise Agents — Complete Runnable Code Examples

Complete TypeScript (`ts/`) and Python (`py/`) implementations accompanying **《企業級 Agent 工程》**.

## Directory Layout

- `ts/` — TypeScript (`@anthropic-ai/sdk` v1.10+, `zod`, Node.js 20+)
  - `shared/types.ts`, `shared/orderops-mock.ts`
  - `ch01/index.ts` .. `ch12/index.ts`
- `py/` — Python (`anthropic` v2.11+, `pydantic`, Python 3.10+)
  - `shared/types.py`, `shared/orderops_mock.py`
  - `ch01/main.py` .. `ch12/main.py`

## Quick Start

```bash
# TypeScript
cd ts && npm install && ANTHROPIC_API_KEY=sk-ant-... npx tsx ch01/index.ts

# Python
cd py && pip install -e . && PYTHONPATH=. ANTHROPIC_API_KEY=sk-ant-... python3 ch01/main.py
```
