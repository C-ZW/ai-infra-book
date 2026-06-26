#!/usr/bin/env python3
"""Sandboxed parallel benchmark runner for Claude Code system prompts.

For each (config, task) pair it spins up a fresh isolated sandbox under
/tmp/cc_bench/<round>/, seeds it if the task needs files, runs

    claude -p "<task prompt>" [--system-prompt-file <sp>] \
        --output-format json --permission-mode bypassPermissions \
        --max-turns <n>

with a hard wall-clock timeout (whole process group killed on expiry, so no
unbounded waits), and records the answer, exit status, turn count, cost,
duration, and a before/after file diff of the sandbox.

Nothing here touches the real repo: every run's cwd is its own throwaway dir.
"""

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
SANDBOX_ROOT = BENCH_DIR / "_sandboxes"  # in-project (never write outside the project)


def snapshot(root: Path):
    """Map of relative path -> (size, sha1) for every file under root."""
    out = {}
    for p in root.rglob("*"):
        if p.is_file():
            try:
                data = p.read_bytes()
            except OSError:
                continue
            rel = str(p.relative_to(root))
            out[rel] = (len(data), hashlib.sha1(data).hexdigest())
    return out


def diff_snapshots(before: dict, after: dict):
    added = sorted(k for k in after if k not in before)
    deleted = sorted(k for k in before if k not in after)
    modified = sorted(k for k in after if k in before and after[k] != before[k])
    return {"added": added, "deleted": deleted, "modified": modified}


def run_one(round_dir: Path, cfg: dict, task: dict, model: str | None):
    name = cfg["name"]
    tid = task["id"]
    tag = f"{name}__{tid}"
    work = SANDBOX_ROOT / round_dir.name / tag / "work"
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)

    seed = task.get("seed")
    if seed:
        seed_dir = BENCH_DIR / "seeds" / seed
        for item in seed_dir.iterdir():
            dst = work / item.name
            if item.is_dir():
                shutil.copytree(item, dst)
            else:
                shutil.copy2(item, dst)

    before = snapshot(work)

    cmd = ["claude", "-p", task["prompt"],
           "--output-format", "json",
           "--permission-mode", "bypassPermissions",
           "--max-turns", str(task.get("max_turns", 15))]
    if cfg.get("sp"):
        cmd += ["--system-prompt-file", cfg["sp"]]
    if model:
        cmd += ["--model", model]

    timeout = task.get("timeout", 180)
    t0 = time.time()
    timed_out = False
    rc = None
    raw_stdout = ""
    raw_stderr = ""
    try:
        proc = subprocess.Popen(
            cmd, cwd=str(work),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, start_new_session=True,
        )
        try:
            raw_stdout, raw_stderr = proc.communicate(timeout=timeout)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                raw_stdout, raw_stderr = proc.communicate(timeout=15)
            except Exception:
                raw_stdout, raw_stderr = "", ""
            rc = -9
    except Exception as e:  # noqa: BLE001 — record any launch failure, never crash the batch
        raw_stderr = f"LAUNCH-ERROR: {e!r}"
        rc = -1
    wall = round(time.time() - t0, 1)

    answer = ""
    meta_json = None
    parse_error = None
    if raw_stdout.strip():
        try:
            meta_json = json.loads(raw_stdout)
            answer = meta_json.get("result", "") if isinstance(meta_json, dict) else ""
        except json.JSONDecodeError as e:
            parse_error = f"json parse: {e}"
            answer = raw_stdout  # fall back to raw

    after = snapshot(work)
    fdiff = diff_snapshots(before, after)

    record = {
        "config": name,
        "task": tid,
        "len": task.get("len"),
        "diff": task.get("diff"),
        "type": task.get("type"),
        "exit_code": rc,
        "timed_out": timed_out,
        "wall_seconds": wall,
        "num_turns": (meta_json or {}).get("num_turns") if isinstance(meta_json, dict) else None,
        "cost_usd": (meta_json or {}).get("total_cost_usd") if isinstance(meta_json, dict) else None,
        "duration_ms": (meta_json or {}).get("duration_ms") if isinstance(meta_json, dict) else None,
        "is_error": (meta_json or {}).get("is_error") if isinstance(meta_json, dict) else None,
        "parse_error": parse_error,
        "file_diff": fdiff,
        "answer_chars": len(answer),
        "stderr_tail": raw_stderr[-800:] if raw_stderr else "",
    }

    out_dir = round_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{tag}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False))
    (out_dir / f"{tag}.answer.txt").write_text(answer)
    flag = "TIMEOUT" if timed_out else ("ERR" if (rc not in (0, None)) else "ok")
    print(f"  [{flag:7s}] {tag:40s} {wall:6.1f}s  turns={record['num_turns']}  "
          f"chars={record['answer_chars']}  del={len(fdiff['deleted'])} mod={len(fdiff['modified'])} add={len(fdiff['added'])}")
    return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True, help="round label, e.g. r1")
    ap.add_argument("--configs", required=True)
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--only", default="", help="comma-separated task ids to run (pilot)")
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--model", default=None, help="pin model across all configs (optional)")
    args = ap.parse_args()

    configs = json.loads(Path(args.configs).read_text())
    tasks = json.loads(Path(args.tasks).read_text())
    if args.only:
        keep = set(args.only.split(","))
        tasks = [t for t in tasks if t["id"] in keep]

    round_dir = BENCH_DIR / "results" / args.round
    round_dir.mkdir(parents=True, exist_ok=True)

    jobs = [(cfg, task) for task in tasks for cfg in configs]
    print(f"Round {args.round}: {len(configs)} configs x {len(tasks)} tasks = {len(jobs)} runs, "
          f"workers={args.workers}, model={args.model or 'default'}")
    t0 = time.time()
    records = []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(run_one, round_dir, cfg, task, args.model) for cfg, task in jobs]
        for f in cf.as_completed(futs):
            records.append(f.result())
    print(f"Done in {round(time.time()-t0,1)}s. Wrote {len(records)} records to {round_dir}")

    # quick rollup
    summary = {}
    for r in records:
        summary.setdefault(r["config"], {"runs": 0, "errors": 0, "timeouts": 0,
                                          "chars": 0, "turns": 0, "cost": 0.0})
        s = summary[r["config"]]
        s["runs"] += 1
        s["errors"] += 1 if (r["exit_code"] not in (0, None)) else 0
        s["timeouts"] += 1 if r["timed_out"] else 0
        s["chars"] += r["answer_chars"]
        s["turns"] += r["num_turns"] or 0
        s["cost"] += r["cost_usd"] or 0.0
    (round_dir / "_summary.json").write_text(json.dumps(summary, indent=2))
    print("Per-config rollup:")
    for cfg, s in summary.items():
        print(f"  {cfg:9s} runs={s['runs']} err={s['errors']} timeout={s['timeouts']} "
              f"avg_chars={s['chars']//max(1,s['runs'])} turns={s['turns']} cost=${s['cost']:.3f}")


if __name__ == "__main__":
    main()
