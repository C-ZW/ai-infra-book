#!/usr/bin/env python3
"""Re-judge existing blind packets with an EXTERNAL model via the `agy` CLI.

Isolates judge-model bias: same blind packets (same candidate answers, same
anonymized labels) as the Claude judges, only the judge changes. Output is saved
in the identical schema under results/<round>/scores_<suffix>/, so the existing
aggregate/compare tooling can consume it.

Usage:
  judge_external.py --round r2 --model "Gemini 3.1 Pro (High)" --suffix gpro --workers 4
"""

import argparse
import concurrent.futures as cf
import json
import re
import subprocess
from pathlib import Path

BENCH = Path(__file__).resolve().parent
INSTR = (BENCH / "judge_instructions.md").read_text()


def _balanced_at(t, start):
    """If a balanced, string-aware JSON object starts at t[start]=='{', return its
    end index (inclusive), else None."""
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(t)):
        c = t[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return i
    return None


def extract_json(text: str):
    """Pull the JSON object containing "scores" out of a noisy model reply.

    Robust to prose-with-braces before/after the JSON: tries every '{' position
    and returns the first balanced object that parses AND contains a "scores"
    key (falling back to the first parseable object, then a fence-stripped whole
    parse)."""
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    first_ok = None
    starts = [i for i, c in enumerate(t) if c == "{"]
    for start in starts:
        end = _balanced_at(t, start)
        if end is None:
            continue
        try:
            obj = json.loads(t[start:end + 1])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "scores" in obj:
            return obj
        if first_ok is None:
            first_ok = obj
    if first_ok is not None:
        return first_ok
    raise ValueError("no parseable JSON object with 'scores' found")


def call_agy(model: str, prompt: str, timeout: int = 150):
    proc = subprocess.run(
        ["agy", "--model", model, "-p", prompt],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, timeout=timeout,
    )
    return proc.stdout, proc.stderr, proc.returncode


def judge_one(model, suffix, round_dir, packet_path, expected_labels):
    tid = packet_path.stem
    packet = packet_path.read_text()
    prompt = (
        INSTR
        + "\n\n=====================  PACKET TO SCORE  =====================\n\n"
        + packet
        + "\n\n=====================  END PACKET  =====================\n\n"
        "Now output ONLY the single JSON object specified above. It must contain a "
        "top-level \"scores\" object mapping EVERY candidate label shown (e.g. "
        f"{', '.join(expected_labels)}) to its five integer dimension scores, an "
        "integer \"overall\", and a short \"rationale\"; plus top-level \"best\" and "
        "\"notes\". No markdown fences, no text before or after the JSON."
    )
    out_dir = round_dir / f"scores_{suffix}"
    out_dir.mkdir(parents=True, exist_ok=True)
    last_err = None
    for attempt in (1, 2):
        try:
            stdout, stderr, rc = call_agy(model, prompt)
            obj = extract_json(stdout)
            got = set(obj.get("scores", {}).keys())
            if not set(expected_labels).issubset(got):
                raise ValueError(f"missing labels: expected {expected_labels}, got {sorted(got)}")
            obj.setdefault("task", tid)
            (out_dir / f"{tid}.json").write_text(json.dumps(obj, indent=2, ensure_ascii=False))
            (out_dir / f"{tid}.raw.txt").write_text(stdout)
            print(f"  [ok ] {suffix:6s} {tid:24s} attempt{attempt} best={obj.get('best')}")
            return True
        except Exception as e:  # noqa: BLE001
            last_err = f"{type(e).__name__}: {e}"
    (out_dir / f"{tid}.ERROR.txt").write_text(f"{last_err}\n\n--- last stdout ---\n{locals().get('stdout','')}")
    print(f"  [FAIL] {suffix:6s} {tid:24s} {last_err}")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--suffix", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    round_dir = BENCH / "results" / args.round
    pdir = round_dir / "packets"
    packets = sorted(pdir.glob("*.md"))
    if args.only:
        keep = set(args.only.split(","))
        packets = [p for p in packets if p.stem in keep]

    jobs = []
    for p in packets:
        key = json.loads((pdir / f"{p.stem}.key.json").read_text())
        jobs.append((p, sorted(key.keys())))

    print(f"Round {args.round} | judge='{args.model}' (suffix={args.suffix}) | {len(jobs)} packets")
    ok = 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(judge_one, args.model, args.suffix, round_dir, p, labels)
                for p, labels in jobs]
        for f in cf.as_completed(futs):
            ok += 1 if f.result() else 0
    print(f"Done: {ok}/{len(jobs)} succeeded for suffix={args.suffix}")


if __name__ == "__main__":
    main()
