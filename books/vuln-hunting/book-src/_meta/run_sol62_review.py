#!/usr/bin/env python3
"""Run codex gpt-6.2-sol (low) technical review & claim verification per chapter,
automatically falling back to agy gemini-4-argon-low on safeguard refusal or error."""
import concurrent.futures
import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path("/Users/theway.chen/Desktop/personal/ai-infra-book")
BOOK_SRC = ROOT / "books/vuln-hunting/book-src"
VERIFY_PROMPT = (ROOT / "tools/md-reader/verify_prompt.md").read_text(encoding="utf-8")
BASELINE = (BOOK_SRC / "_meta/running-examples.md").read_text(encoding="utf-8")
LANDSCAPE = (BOOK_SRC / "_meta/landscape-2026-11.md").read_text(encoding="utf-8")
EFFORT = os.environ.get("CODEX_EFFORT", "low")
OUT_PATH = BOOK_SRC / f"_meta/review-sol62-{EFFORT}-report.json"
CACHE_DIR = BOOK_SRC / f"_meta/review-sol62-{EFFORT}-cache"

SAFEGUARD_MARKERS = (
    "blocked by",
    "content safety",
    "safeguard",
    "cannot assist",
    "can't assist",
    "i'm sorry",
    "i cannot",
    "policy",
    "refuse",
)


def parse_json_payload(raw: str):
    text = raw.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    data = json.loads(text)
    if not isinstance(data, dict) or data.get("status") != "complete" or not isinstance(data.get("claims"), list):
        raise ValueError("Invalid review JSON schema")
    return data


def run_codex(prompt: str, timeout: int = 180):
    with tempfile.TemporaryDirectory(prefix="sol62-rev-") as tmp:
        out_file = Path(tmp) / "out.json"
        cmd = [
            "codex", "exec", "--skip-git-repo-check", "--ephemeral",
            "--sandbox", "read-only",
            "-m", "gpt-6.2-sol",
            "-c", f'model_reasoning_effort="{EFFORT}"',
            "--output-last-message", str(out_file),
            "-",
        ]
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=tmp, start_new_session=True,
        )
        try:
            stdout, stderr = proc.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            return None, f"timeout after {timeout}s", False
        raw = out_file.read_text(encoding="utf-8") if out_file.exists() else stdout
        low = (raw + "\n" + stderr).lower()
        is_safeguard = any(m in low for m in SAFEGUARD_MARKERS) and (proc.returncode != 0 or not raw.strip().startswith("{"))
        if proc.returncode != 0:
            return None, f"codex exit {proc.returncode} (safeguard={is_safeguard})", is_safeguard
        try:
            return parse_json_payload(raw), None, False
        except Exception as e:
            return None, f"codex parse error: {e} (safeguard={is_safeguard})", is_safeguard


def run_argon(prompt: str, timeout: int = 180):
    with tempfile.TemporaryDirectory(prefix="argon-rev-") as tmp:
        cmd = [
            "agy", "--model", "gemini-4-argon-low",
            "--output-format", "text",
            "--print", prompt,
        ]
        proc = subprocess.Popen(
            cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=tmp, start_new_session=True,
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            return None, f"argon timeout after {timeout}s"
        if proc.returncode != 0:
            return None, f"argon exit {proc.returncode}"
        try:
            return parse_json_payload(stdout), None
        except Exception as e:
            return None, f"argon parse error: {e}"


def review_chapter(ch_path: Path):
    cache_dir = CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{ch_path.stem}.json"
    if cache_file.is_file():
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
        if cached.get("status") == "complete":
            return cached
    text = ch_path.read_text(encoding="utf-8")
    ev_path = BOOK_SRC / "_meta/source-evidence" / f"{ch_path.stem}.md"
    ev = ev_path.read_text(encoding="utf-8") if ev_path.is_file() else LANDSCAPE
    prompt = (
        VERIFY_PROMPT
        + "\n\n<baseline>\n" + BASELINE + "\n</baseline>"
        + "\n<source-evidence>\n" + ev + "\n</source-evidence>"
        + "\n<chapter>\n" + text + "\n</chapter>"
    )
    res, err, is_sg = run_codex(prompt, timeout=240)
    if res is not None:
        out = {
            "chapter": ch_path.name,
            "reviewer": f"codex:gpt-6.2-sol:{EFFORT}",
            "fallback_used": False,
            "status": "complete",
            "claims": res["claims"],
        }
        cache_file.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return out
    # Fallback to gemini-4-argon-low
    res2, err2 = run_argon(prompt)
    if res2 is not None:
        out = {
            "chapter": ch_path.name,
            "reviewer": "agy:gemini-4-argon-low",
            "fallback_used": True,
            "fallback_reason": err,
            "status": "complete",
            "claims": res2["claims"],
        }
        cache_file.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return out
    return {
        "chapter": ch_path.name,
        "reviewer": "none",
        "fallback_used": True,
        "status": "error",
        "error": f"codex={err}; argon={err2}",
        "claims": [],
    }


def main():
    selected = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    chapters = sorted(BOOK_SRC.glob("ch*.md"))
    if selected:
        chapters = [p for p in chapters if p.stem in selected or p.name in selected or p.name[:4] in selected]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(review_chapter, p): p for p in chapters}
        for fut in concurrent.futures.as_completed(futs):
            r = fut.result()
            results.append(r)
            bad = [c for c in r["claims"] if c.get("verdict") != "correct"]
            print(
                f"[{len(results)}/{len(chapters)}] {r['chapter']} -> {r['reviewer']} "
                f"status={r['status']} claims={len(r['claims'])} non_correct={len(bad)}",
                flush=True,
            )
    results.sort(key=lambda x: x["chapter"])
    summary = {
        "total": len(results),
        "complete": sum(1 for r in results if r["status"] == "complete"),
        "codex_reviewed": sum(1 for r in results if r["reviewer"].startswith("codex:gpt-6.2-sol:")),
        "argon_fallback": sum(1 for r in results if r["reviewer"] == "agy:gemini-4-argon-low"),
        "errors": sum(1 for r in results if r["status"] != "complete"),
        "incorrect_claims": sum(
            1 for r in results for c in r["claims"] if c.get("verdict") == "incorrect"
        ),
        "imprecise_claims": sum(
            1 for r in results for c in r["claims"] if c.get("verdict") == "imprecise"
        ),
        "chapters": results,
    }
    OUT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"DONE: {json.dumps({k: v for k, v in summary.items() if k != 'chapters'}, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
