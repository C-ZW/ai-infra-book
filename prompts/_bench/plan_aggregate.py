#!/usr/bin/env python3
"""De-anonymize PLAN judge scores and roll up per-config planning means."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

BENCH = Path(__file__).resolve().parent
DIMS = ["decomposition", "sequencing", "completeness", "verification", "risk_handling", "discipline"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    args = ap.parse_args()
    rdir = BENCH / "results" / args.round
    sdir, pdir = rdir / "scores", rdir / "packets"

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
            dvals = []
            for d in DIMS:
                v = sc.get(d)
                if isinstance(v, (int, float)):
                    by_cfg[cfg][d].append(v); dvals.append(v)
            ov = sc.get("overall")
            if not isinstance(ov, (int, float)) and dvals:
                ov = sum(dvals) / len(dvals)
            if isinstance(ov, (int, float)):
                overall[cfg].append(ov)
            row[cfg] = {"overall": round(ov, 2) if isinstance(ov, (int, float)) else None,
                        **{d: sc.get(d) for d in DIMS}}
        b = scores.get("best")
        if b in key:
            wins[key[b]] += 1
        per_task[tid] = {"by_config": row, "best": key.get(b) if b else None, "notes": scores.get("notes", "")}

    configs = sorted(by_cfg)
    print(f"\n=== Round {args.round} — PLAN quality per-config means ===\n")
    header = f"{'config':9s} " + " ".join(f"{d[:6]:>7s}" for d in DIMS) + f" {'OVERALL':>8s} {'wins':>5s}"
    print(header); print("-" * len(header))
    rollup = {}
    for cfg in configs:
        dm = {d: (round(sum(by_cfg[cfg][d]) / len(by_cfg[cfg][d]), 2) if by_cfg[cfg][d] else None) for d in DIMS}
        ov = round(sum(overall[cfg]) / len(overall[cfg]), 3) if overall[cfg] else None
        rollup[cfg] = {"dims": dm, "overall": ov, "wins": wins[cfg], "n": len(overall[cfg])}
        cells = " ".join(f"{dm[d] if dm[d] is not None else '-':>7}" for d in DIMS)
        print(f"{cfg:9s} {cells} {ov if ov is not None else '-':>8} {wins[cfg]:>5}")
    (rdir / "_scores.json").write_text(json.dumps({"round": args.round, "rollup": rollup, "per_task": per_task}, indent=2, ensure_ascii=False))
    print(f"\nWrote {rdir/'_scores.json'}")


if __name__ == "__main__":
    main()
