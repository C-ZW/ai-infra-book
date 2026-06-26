#!/usr/bin/env python3
"""De-anonymize judge scores and roll up per-config means.

Reads results/<round>/scores/<task>.json (judge output, keyed by anonymous
label) + results/<round>/packets/<task>.key.json (label→config), and emits a
per-config × per-dimension score table plus an overall mean and win counts.
Dimensions can be null (e.g. tool-discipline on a pure-text task) and are
skipped in the means.
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

BENCH = Path(__file__).resolve().parent
DIMS = ["instruction_following", "correctness", "conciseness", "tool_discipline", "safety"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    args = ap.parse_args()
    rdir = BENCH / "results" / args.round
    sdir = rdir / "scores"
    pdir = rdir / "packets"

    # config -> dim -> list of scores ; config -> list of per-task overall
    by_cfg = defaultdict(lambda: defaultdict(list))
    overall = defaultdict(list)
    wins = defaultdict(int)
    per_task = {}

    for sf in sorted(sdir.glob("*.json")):
        tid = sf.stem
        scores = json.loads(sf.read_text())
        key = json.loads((pdir / f"{tid}.key.json").read_text())
        row = {}
        for label, cfg in key.items():
            sc = scores["scores"].get(label, {})
            dim_vals = []
            for d in DIMS:
                v = sc.get(d)
                if isinstance(v, (int, float)):
                    by_cfg[cfg][d].append(v)
                    dim_vals.append(v)
            ov = sc.get("overall")
            if not isinstance(ov, (int, float)) and dim_vals:
                ov = sum(dim_vals) / len(dim_vals)
            if isinstance(ov, (int, float)):
                overall[cfg].append(ov)
            row[cfg] = {"overall": round(ov, 2) if isinstance(ov, (int, float)) else None,
                        **{d: sc.get(d) for d in DIMS}}
        best_label = scores.get("best")
        if best_label and best_label in key:
            wins[key[best_label]] += 1
        per_task[tid] = {"by_config": row, "best": key.get(best_label) if best_label else None,
                         "notes": scores.get("notes", "")}

    configs = sorted(by_cfg.keys())
    print(f"\n=== Round {args.round} — per-config means ===\n")
    header = f"{'config':10s} " + " ".join(f"{d[:6]:>7s}" for d in DIMS) + f" {'OVERALL':>8s} {'wins':>5s}"
    print(header)
    print("-" * len(header))
    rollup = {}
    for cfg in configs:
        dim_means = {}
        for d in DIMS:
            vals = by_cfg[cfg][d]
            dim_means[d] = round(sum(vals) / len(vals), 2) if vals else None
        ov = round(sum(overall[cfg]) / len(overall[cfg]), 3) if overall[cfg] else None
        rollup[cfg] = {"dims": dim_means, "overall": ov, "wins": wins[cfg], "n": len(overall[cfg])}
        cells = " ".join(f"{(dim_means[d] if dim_means[d] is not None else '-'):>7}" for d in DIMS)
        print(f"{cfg:10s} {cells} {ov if ov is not None else '-':>8} {wins[cfg]:>5}")

    out = {"round": args.round, "rollup": rollup, "per_task": per_task}
    (rdir / "_scores.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nWrote {rdir / '_scores.json'}")


if __name__ == "__main__":
    main()
