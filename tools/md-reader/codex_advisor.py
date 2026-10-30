#!/usr/bin/env python3
"""Run codex as validator and advisor for book chapters."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
BOOK_SRC = PROJECT_ROOT / "books" / "question-genesis" / "book-src"
OUTPUT_DIR = BOOK_SRC / "_meta" / "codex-audit"

PROMPT_TEMPLATE = """You are a rigorous factual auditor, mathematical reviewer, and stylistic advisor for a technical narrative book ("問題誕生之前：從理所當然到值得追問").

Examine the following chapter:
1. Verify all load-bearing historical claims, dates, names, numbers, experimental settings, and citations against historical facts.
2. Verify any mathematical, statistical, or logical derivations for soundness.
3. Identify any fragile claims, popular myths that need disclaimers, or factual inaccuracies.
4. Provide constructive advice on whether the chapter meets the high standards of serious non-fiction.

Output ONLY valid JSON in the following format:
```json
{
  "chapter": "{chapter_id}",
  "verdict": "PASS" | "NEEDS_REVISION",
  "historical_accuracy": "accurate" | "minor_issues" | "inaccurate",
  "logic_soundness": "sound" | "flawed",
  "findings": [
    {
      "claim": "The exact claim or sentence in text",
      "verdict": "correct" | "imprecise" | "incorrect",
      "reasoning": "Detailed factual or logical evaluation",
      "recommendation": "Suggested adjustment, or 'none' if correct"
    }
  ],
  "advisory_summary": "Overall assessment and recommendations"
}
```

Chapter text to review:
{chapter_text}
"""

def audit_chapter(chapter_path: Path) -> dict:
    stem = chapter_path.stem
    cid = stem.split("-")[0]
    text = chapter_path.read_text(encoding="utf-8")
    prompt = PROMPT_TEMPLATE.replace("{chapter_id}", cid).replace("{chapter_text}", text)
    
    cmd = [
        "codex", "exec",
        "--skip-git-repo-check",
        "--ephemeral",
        "--sandbox", "read-only",
        "-m", "gpt-6.1-terra",
        "-c", "model_reasoning_effort=\"medium\"",
        "-"
    ]
    
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate(prompt, timeout=300)
    
    if proc.returncode != 0:
        return {
            "chapter": cid,
            "verdict": "ERROR",
            "error": f"codex exited with {proc.returncode}: {stderr[:200]}"
        }
    
    # Extract JSON
    raw = stdout.strip()
    if "```json" in raw:
        raw = raw.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in raw:
        raw = raw.split("```", 1)[1].split("```", 1)[0].strip()
        
    try:
        data = json.loads(raw)
        return data
    except Exception as exc:
        return {
            "chapter": cid,
            "verdict": "PARSE_ERROR",
            "error": str(exc),
            "raw_output": stdout[:500]
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapters", nargs="+", help="Chapter IDs e.g. ch13 ch14")
    args = parser.parse_args()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.chapters:
        target_ids = set(args.chapters)
        files = [f for f in sorted(BOOK_SRC.glob("ch*.md")) if f.stem.split("-")[0] in target_ids]
    else:
        files = sorted(BOOK_SRC.glob("ch*.md"))
        
    print(f"Running Codex Advisor on {len(files)} chapters...")
    summary = {}
    for f in files:
        cid = f.stem.split("-")[0]
        print(f"Auditing {cid} ({f.name})...", flush=True)
        res = audit_chapter(f)
        out_file = OUTPUT_DIR / f"{cid}.json"
        out_file.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        verdict = res.get("verdict", "UNKNOWN")
        print(f"  -> {cid}: {verdict}")
        summary[cid] = verdict
        
    print("\nAudit Summary:")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
