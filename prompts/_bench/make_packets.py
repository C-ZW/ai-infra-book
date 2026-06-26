#!/usr/bin/env python3
"""Build blind, shuffled judge packets from a round's results.

For each task it gathers every config's answer + behavioral telemetry, shuffles
them into anonymous labels (A/B/C…) with a per-task deterministic seed, and
writes a self-contained markdown packet the judge can score without knowing
which system prompt produced which answer. A sibling .key.json records the
label→config mapping for later de-anonymization.
"""

import argparse
import hashlib
import json
import random
from pathlib import Path

BENCH = Path(__file__).resolve().parent


def seeded(task_id):
    return random.Random(int(hashlib.sha1(task_id.encode()).hexdigest(), 16) % (10 ** 9))


def _clean(paths):
    """Drop test/byte-cache artifacts that aren't real source edits."""
    noise = ("__pycache__", ".pytest_cache", ".pyc")
    return [p for p in paths if not any(n in p for n in noise)]


def telemetry(rec):
    fd = dict(rec.get("file_diff", {}))
    fd = {k: _clean(fd.get(k, [])) for k in ("added", "modified", "deleted")}
    parts = [
        f"exit={rec.get('exit_code')}",
        f"timed_out={rec.get('timed_out')}",
        f"turns={rec.get('num_turns')}",
        f"wall={rec.get('wall_seconds')}s",
        f"answer_chars={rec.get('answer_chars')}",
        f"files_added={fd.get('added', [])}",
        f"files_modified={fd.get('modified', [])}",
        f"files_deleted={fd.get('deleted', [])}",
    ]
    return "; ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    ap.add_argument("--tasks", default=str(BENCH / "tasks.json"))
    args = ap.parse_args()

    tasks = {t["id"]: t for t in json.loads(Path(args.tasks).read_text())}
    rdir = BENCH / "results" / args.round
    pdir = rdir / "packets"
    pdir.mkdir(parents=True, exist_ok=True)

    accept_path = rdir / "_acceptance.json"
    acceptance = json.loads(accept_path.read_text()) if accept_path.exists() else {}

    # discover configs present
    recs_by_task = {}
    for j in sorted(rdir.glob("*__*.json")):
        if j.name.startswith("_"):
            continue
        rec = json.loads(j.read_text())
        tid = rec["task"]
        recs_by_task.setdefault(tid, []).append(rec)

    built = []
    for tid, recs in recs_by_task.items():
        task = tasks[tid]
        rng = seeded(tid)
        rng.shuffle(recs)
        labels = [chr(ord("A") + i) for i in range(len(recs))]
        key = {}
        sections = []
        for label, rec in zip(labels, recs):
            key[label] = rec["config"]
            answer = (rdir / f"{rec['config']}__{tid}.answer.txt").read_text()
            acc = acceptance.get(tid, {}).get(rec["config"])
            acc_line = ""
            if acc:
                bits = {k: v for k, v in acc.items() if k not in ("config", "task")}
                acc_line = f"Objective acceptance (ground truth): {json.dumps(bits)}\n\n"
            sections.append(
                f"### Candidate {label}\n\n"
                f"Behavioral telemetry: {telemetry(rec)}\n\n"
                f"{acc_line}"
                f"Answer:\n````\n{answer.strip() or '(empty answer)'}\n````\n"
            )
        packet = (
            f"# Judge packet — task `{tid}` ({task['len']}/{task['diff']}, {task['type']})\n\n"
            f"## The task given to each candidate\n\n> {task['prompt']}\n\n"
            f"## What to reward / penalize\n\n{task['rubric_focus']}\n\n"
            f"## Candidates (anonymized, order randomized)\n\n"
            + "\n".join(sections)
        )
        (pdir / f"{tid}.md").write_text(packet)
        (pdir / f"{tid}.key.json").write_text(json.dumps(key, indent=2))
        built.append((tid, key))

    print(f"Built {len(built)} packets in {pdir}")
    for tid, key in built:
        print(f"  {tid}: " + ", ".join(f"{k}={v}" for k, v in key.items()))


if __name__ == "__main__":
    main()
