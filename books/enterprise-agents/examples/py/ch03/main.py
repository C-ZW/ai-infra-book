"""Chapter 03: Context Engineering, Prompt Caching prefix layering, Extended Thinking, and Compaction."""

from __future__ import annotations

import html
import os
import sys
from pathlib import Path
from typing import Any

# Ensure `shared` package is importable when running `python main.py` directly
EXAMPLES_PY_DIR = Path(__file__).resolve().parent.parent
if str(EXAMPLES_PY_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_PY_DIR))

from shared.types import calculate_cost_usd  # noqa: E402

SAMPLE_TICKET: dict[str, Any] = {
    "ticket_id": "TKT-2026-0301",
    "tenant_id": "tenant-apac-01",
    "customer_id": "CUST-9012",
    "order_id": "ORD-2026-88412",
    "category": "shipping_delay",
    "priority": "high",
    "subject": "Order ORD-2026-88412 delayed past promised date",
    "body": "Promised delivery was 2026-11-18, tracking TRK-99812344 has not updated.",
    "created_at": "2026-11-21T10:00:00Z",
}

MODEL = "claude-sonnet-5-5"
THINKING_BUDGET_TOKENS = 4000  # Ledger demo assumption for billed thinking tokens
MAX_TOKENS = 8000
TOOL_RESULT_MAX_CHARS = 2400  # Rough estimate: ~600 tokens


def build_layered_prompt(
    ticket: dict[str, Any],
    tools: list[dict[str, Any]],
    static_policy: str,
) -> dict[str, Any]:
    """Build a cache-friendly prompt in strict prefix order: tools -> system -> messages."""
    cached_tools = []
    for idx, tool in enumerate(tools):
        item = dict(tool)
        if idx == len(tools) - 1:
            item["cache_control"] = {"type": "ephemeral"}
        cached_tools.append(item)

    system = [
        {
            "type": "text",
            "text": static_policy,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    dynamic_user_content = (
        "<ticket_context>\n"
        f"  <ticket_id>{html.escape(str(ticket['ticket_id']))}</ticket_id>\n"
        f"  <tenant_id>{html.escape(str(ticket['tenant_id']))}</tenant_id>\n"
        f"  <order_id>{html.escape(str(ticket['order_id']))}</order_id>\n"
        f"  <category>{html.escape(str(ticket['category']))}</category>\n"
        f"  <priority>{html.escape(str(ticket['priority']))}</priority>\n"
        f"  <created_at>{html.escape(str(ticket['created_at']))}</created_at>\n"
        f"  <subject>{html.escape(str(ticket['subject']))}</subject>\n"
        f"  <body>{html.escape(str(ticket['body']))}</body>\n"
        "</ticket_context>"
    )

    return {
        "tools": cached_tools,
        "system": system,
        "messages": [{"role": "user", "content": dynamic_user_content}],
    }


def truncate_tool_result(raw_output: str, max_chars: int = TOOL_RESULT_MAX_CHARS) -> str:
    """Truncate oversized tool output (~8,000 tokens) down to ~600 tokens."""
    if len(raw_output) <= max_chars:
        return raw_output
    if max_chars <= 0:
        return ""
    head_len = int(max_chars * 0.7)
    tail_len = int(max_chars * 0.2)
    head = raw_output[:head_len] if head_len > 0 else ""
    tail = raw_output[-tail_len:] if tail_len > 0 else ""
    omitted = len(raw_output) - len(head) - len(tail)
    marker = f"\n...[truncated {omitted} chars]...\n"
    if len(head) + len(tail) + len(marker) > max_chars:
        return raw_output[:max_chars]
    return f"{head}{marker}{tail}"


def _summarize_content(content: Any) -> str:
    if isinstance(content, str):
        return content[:120]
    parts: list[str] = []
    for block in content:
        btype = block.get("type") if isinstance(block, dict) else getattr(block, "type", "unknown")
        if btype == "text":
            text = block.get("text", "") if isinstance(block, dict) else getattr(block, "text", "")
            parts.append(text[:80])
        elif btype == "tool_use":
            name = block.get("name", "") if isinstance(block, dict) else getattr(block, "name", "")
            parts.append(f"[tool_use:{name}]")
        elif btype == "tool_result":
            tid = block.get("tool_use_id", "") if isinstance(block, dict) else getattr(block, "tool_use_id", "")
            parts.append(f"[tool_result:{tid}]")
        else:
            parts.append(f"[{btype}]")
    return " ".join(parts)


def compact_history(
    messages: list[dict[str, Any]],
    keep_recent_turns: int = 2,
) -> list[dict[str, Any]]:
    """Compact older turns into a structured summary while keeping recent turns intact."""
    keep_count = keep_recent_turns * 2
    if len(messages) <= keep_count + 1:
        return messages

    split_idx = len(messages) - keep_count
    # Avoid splitting an assistant tool_use from its following user tool_result
    while split_idx > 1 and messages[split_idx].get("role") == "user" and isinstance(messages[split_idx].get("content"), list):
        split_idx -= 1
    if split_idx <= 1:
        return messages

    first_user = messages[0]
    middle = messages[1:split_idx]
    recent = messages[split_idx:]

    summary_lines: list[str] = []
    for idx, msg in enumerate(middle, start=1):
        preview = _summarize_content(msg.get("content", ""))
        summary_lines.append(f"- Turn {idx} ({msg['role']}): {' '.join(preview.split())}")

    compacted_block = {
        "role": "user",
        "content": "<compacted_history>\n" + "\n".join(summary_lines) + "\n</compacted_history>",
    }
    return [first_user, compacted_block, *recent]


def main() -> None:
    static_policy = (
        "<role>\n"
        "You are OrderOps Triage Agent. Resolve customer and supplier exception tickets\n"
        "using only verified tool outputs.\n"
        "</role>\n"
        "<rules>\n"
        "1. Never invent order amounts, tracking numbers, or refund approvals.\n"
        "2. Always check order status before proposing a refund.\n"
        "</rules>"
    )
    sample_tools = [
        {
            "name": "get_order",
            "description": "Fetch order details by order_id.",
            "input_schema": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
        }
    ]

    prompt = build_layered_prompt(SAMPLE_TICKET, sample_tools, static_policy)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[ch03] ANTHROPIC_API_KEY not set; running offline verification.")
        big_log = "ERP_EVENT " * 3200
        truncated = truncate_tool_result(big_log)
        print(f"Truncated tool output: {len(big_log)} -> {len(truncated)} chars")

        mock_history = [
            *prompt["messages"],
            {"role": "assistant", "content": [{"type": "tool_use", "id": "toolu_1", "name": "get_order", "input": {"order_id": "ORD-2026-88412"}}]},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": truncated}]},
            {"role": "assistant", "content": "Checked order status."},
            {"role": "user", "content": "Please check refund eligibility."},
            {"role": "assistant", "content": "Checking refund policy."},
        ]
        compacted = compact_history(mock_history)
        print(f"Compacted history: {len(mock_history)} -> {len(compacted)} messages")

        # Ledger demonstration (assumes 6,000-token prefix write + 4,000 billed thinking tokens)
        cost = calculate_cost_usd(
            MODEL,
            input_tokens=1200,
            output_tokens=350 + THINKING_BUDGET_TOKENS,
            cache_creation_input_tokens=6000,
            cache_read_input_tokens=0,
        )
        print(f"Estimated Turn-1 cost with Extended Thinking (ledger demo): ${cost:.6f}")
        return

    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        thinking={"type": "adaptive"},
        tools=prompt["tools"],
        system=prompt["system"],
        messages=prompt["messages"],
    )

    # Preserve thinking blocks + signature verbatim in multi-turn history
    updated = [*prompt["messages"], {"role": "assistant", "content": response.content}]
    compacted = compact_history(updated)
    cost = calculate_cost_usd(
        MODEL,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        cache_creation_input_tokens=getattr(response.usage, "cache_creation_input_tokens", 0) or 0,
        cache_read_input_tokens=getattr(response.usage, "cache_read_input_tokens", 0) or 0,
    )
    print("stop_reason:", response.stop_reason)
    print("messages after compaction:", len(compacted))
    print(f"turn cost (USD): {cost:.6f}")


if __name__ == "__main__":
    main()
