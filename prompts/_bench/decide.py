#!/usr/bin/env python3
"""Apply the convergence stop-rule to a round's scores.

Compares a NEW config against the PRIOR-BEST config within the same round
(both judged in the same blind packets, so the comparison controls for run and
judge variance). Prints the per-dimension and overall deltas and a verdict:

- NEW_WINS    : new beats prior-best on overall by > MARGIN  -> keep iterating
- CONVERGED   : overall gain <= MARGIN and new loses no dimension by > DIM_TOL
                -> "no significant difference", stop
- REGRESSION  : new is worse on overall by > MARGIN          -> discard, stop/retry

Usage: decide.py --round r2 --new v2 --best v1
"""

import argparse
import json
from pathlib import Path

BENCH = Path(__file__).resolve().parent
DIMS = ["instruction_following", "correctness", "conciseness", "tool_discipline", "safety"]
MARGIN = 0.20    # overall delta below this = "no significant difference"
DIM_TOL = 0.30   # a dimension regression larger than this blocks a CONVERGED verdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--best", required=True)
    args = ap.parse_args()

    data = json.loads((BENCH / "results" / args.round / "_scores.json").read_text())
    roll = data["rollup"]
    new, best = roll[args.new], roll[args.best]

    d_overall = round((new["overall"] or 0) - (best["overall"] or 0), 3)
    print(f"\n=== Convergence check (round {args.round}): {args.new} vs prior-best {args.best} ===\n")
    print(f"  overall: {args.new}={new['overall']}  {args.best}={best['overall']}  "
          f"delta={d_overall:+.3f}  (margin={MARGIN})")
    print(f"  wins:    {args.new}={new['wins']}  {args.best}={best['wins']}")
    print("  per-dimension delta (new - best):")
    worst_dim_drop = 0.0
    for dim in DIMS:
        nv, bv = new["dims"].get(dim), best["dims"].get(dim)
        if nv is None or bv is None:
            print(f"    {dim:22s} n/a")
            continue
        dd = round(nv - bv, 3)
        worst_dim_drop = min(worst_dim_drop, dd)
        flag = "  <-- regression" if dd < -DIM_TOL else ""
        print(f"    {dim:22s} {args.new}={nv:<5} {args.best}={bv:<5} delta={dd:+.3f}{flag}")

    if d_overall > MARGIN:
        verdict = "NEW_WINS — new prompt significantly beats prior best; keep iterating."
    elif d_overall < -MARGIN:
        verdict = "REGRESSION — new prompt is worse; discard and stop/retry."
    elif worst_dim_drop < -DIM_TOL:
        verdict = (f"MIXED — overall within margin but a dimension regressed by "
                   f"{worst_dim_drop:+.2f}; not a clean convergence.")
    else:
        verdict = "CONVERGED — no significant difference vs prior best. STOP."
    print(f"\n  VERDICT: {verdict}\n")


if __name__ == "__main__":
    main()
