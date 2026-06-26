#!/usr/bin/env python3
"""Pool multiple rounds' judge scores into combined per-config means.

Single-replicate-per-task judging is noisy (the identical prompt was seen to
swing ~0.25 in overall between rounds). Pooling N rounds gives N replicates per
task and roughly halves the standard error, so a v2-vs-v1 decision rests on
16 task-judgments per config instead of 8.

Usage: pool.py --rounds r2 r3 --configs v1 v2 default
"""

import argparse
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

BENCH = Path(__file__).resolve().parent
DIMS = ["instruction_following", "correctness", "conciseness", "tool_discipline", "safety"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", nargs="+", required=True)
    ap.add_argument("--configs", nargs="+", required=True)
    args = ap.parse_args()

    dim_vals = defaultdict(lambda: defaultdict(list))   # cfg -> dim -> [..]
    overalls = defaultdict(list)                         # cfg -> [per-task overall]
    wins = defaultdict(int)
    n_tasks = 0

    for rnd in args.rounds:
        data = json.loads((BENCH / "results" / rnd / "_scores.json").read_text())
        for tid, info in data["per_task"].items():
            n_tasks += 1
            for cfg in args.configs:
                bc = info["by_config"].get(cfg)
                if not bc:
                    continue
                for d in DIMS:
                    v = bc.get(d)
                    if isinstance(v, (int, float)):
                        dim_vals[cfg][d].append(v)
                ov = bc.get("overall")
                if isinstance(ov, (int, float)):
                    overalls[cfg].append(ov)
            if info.get("best") in args.configs:
                wins[info["best"]] += 1

    print(f"\n=== Pooled over rounds {args.rounds} ({n_tasks} task-judgments total) ===\n")
    header = f"{'config':9s} " + " ".join(f"{d[:6]:>7s}" for d in DIMS) + f" {'OVERALL':>8s} {'sd':>5s} {'n':>3s} {'wins':>5s}"
    print(header); print("-" * len(header))
    out = {}
    for cfg in args.configs:
        dm = {d: round(st.mean(dim_vals[cfg][d]), 3) if dim_vals[cfg][d] else None for d in DIMS}
        ov = round(st.mean(overalls[cfg]), 3) if overalls[cfg] else None
        sd = round(st.pstdev(overalls[cfg]), 3) if len(overalls[cfg]) > 1 else 0.0
        out[cfg] = {"dims": dm, "overall": ov, "sd": sd, "n": len(overalls[cfg]), "wins": wins[cfg]}
        cells = " ".join(f"{dm[d] if dm[d] is not None else '-':>7}" for d in DIMS)
        print(f"{cfg:9s} {cells} {ov:>8} {sd:>5} {len(overalls[cfg]):>3} {wins[cfg]:>5}")

    # decision: best two by overall
    ranked = sorted([c for c in args.configs if out[c]["overall"] is not None],
                    key=lambda c: out[c]["overall"], reverse=True)
    if len(ranked) >= 2:
        a, b = ranked[0], ranked[1]
        d = round(out[a]["overall"] - out[b]["overall"], 3)
        # pooled standard error of the difference (independent task samples)
        import math
        sea = out[a]["sd"] / math.sqrt(max(1, out[a]["n"]))
        seb = out[b]["sd"] / math.sqrt(max(1, out[b]["n"]))
        sediff = round(math.sqrt(sea**2 + seb**2), 3)
        print(f"\nTop two: {a}={out[a]['overall']} vs {b}={out[b]['overall']}  "
              f"delta={d:+.3f}  SE(diff)~{sediff}  ({d/sediff:+.2f} SE)" if sediff else "")
        sig = abs(d) > 2 * sediff and abs(d) > 0.2
        print(f"VERDICT: {'SIGNIFICANT — ' + a + ' wins' if sig else 'NO SIGNIFICANT DIFFERENCE (converged)'}")
    (BENCH / "results" / "pooled_scores.json").write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
