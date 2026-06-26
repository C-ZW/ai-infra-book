#!/usr/bin/env python3
"""Cross-judge agreement analysis: do independent judge models agree on v2 vs v1?

Reads the same blind packets scored by several judges (Claude = scores/, plus
external models in scores_<suffix>/), de-anonymizes via the key files, pools the
given rounds, and prints, per judge, the v2-vs-v1 overall delta, the conciseness
delta, and head-to-head win counts — then a concordance verdict.

Usage:
  cross_compare.py --rounds r2 r3 \
    --judges claude:scores gpro:scores_gpro gflash:scores_gflash gptoss:scores_gptoss
"""

import argparse
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

BENCH = Path(__file__).resolve().parent
DIMS = ["instruction_following", "correctness", "conciseness", "tool_discipline", "safety"]
CONFIGS = ["v2", "v1", "default"]


def load_judge(rounds, subdir):
    """Return (overall[cfg]->[..], concise[cfg]->[..], wins[cfg]->int, n_tasks)."""
    overall = defaultdict(list)
    concise = defaultdict(list)
    wins = defaultdict(int)
    n = 0
    for rnd in rounds:
        rdir = BENCH / "results" / rnd
        sdir = rdir / subdir
        pdir = rdir / "packets"
        for kf in sorted(pdir.glob("*.key.json")):
            tid = kf.name[:-len(".key.json")]
            sf = sdir / f"{tid}.json"
            if not sf.exists():
                continue
            key = json.loads(kf.read_text())          # label -> config
            sc = json.loads(sf.read_text())
            n += 1
            for label, cfg in key.items():
                s = sc.get("scores", {}).get(label, {})
                ov = s.get("overall")
                if not isinstance(ov, (int, float)):
                    dvals = [s.get(d) for d in DIMS if isinstance(s.get(d), (int, float))]
                    ov = sum(dvals) / len(dvals) if dvals else None
                if isinstance(ov, (int, float)):
                    overall[cfg].append(ov)
                cv = s.get("conciseness")
                if isinstance(cv, (int, float)):
                    concise[cfg].append(cv)
            best = sc.get("best")
            if best in key:
                wins[key[best]] += 1
    return overall, concise, wins, n


def mean(xs):
    return round(st.mean(xs), 3) if xs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", nargs="+", required=True)
    ap.add_argument("--judges", nargs="+", required=True, help="name:subdir pairs")
    args = ap.parse_args()

    print(f"\n=== Cross-judge agreement (pooled {args.rounds}) — v2 vs v1 ===\n")
    hdr = f"{'judge':9s} {'family':8s} | {'v2_ov':>6s} {'v1_ov':>6s} {'dOv':>6s} | {'v2_cc':>6s} {'v1_cc':>6s} {'dCc':>6s} | {'wins v2/v1/def':>14s}"
    print(hdr); print("-" * len(hdr))

    family = {"claude": "Claude", "gpro": "Gemini", "gflash": "Gemini",
              "gptoss": "GPT-OSS"}
    summary = {}
    concord_overall = []
    concord_concise = []
    for spec in args.judges:
        name, subdir = spec.split(":", 1)
        ov, cc, wins, n = load_judge(args.rounds, subdir)
        v2o, v1o = mean(ov["v2"]), mean(ov["v1"])
        v2c, v1c = mean(cc["v2"]), mean(cc["v1"])
        d_ov = round((v2o or 0) - (v1o or 0), 3)
        d_cc = round((v2c or 0) - (v1c or 0), 3)
        summary[name] = {"family": family.get(name, name), "n": n,
                         "v2_overall": v2o, "v1_overall": v1o, "d_overall": d_ov,
                         "v2_concise": v2c, "v1_concise": v1c, "d_concise": d_cc,
                         "wins": {c: wins[c] for c in CONFIGS}}
        concord_overall.append(d_ov)
        concord_concise.append(d_cc)
        print(f"{name:9s} {family.get(name,name):8s} | {v2o:>6} {v1o:>6} {d_ov:>+6.2f} | "
              f"{v2c:>6} {v1c:>6} {d_cc:>+6.2f} | {wins['v2']:>4}/{wins['v1']}/{wins['default']:<6}")

    print("\nConcordance:")
    print(f"  overall delta (v2-v1) across judges: {[f'{d:+.2f}' for d in concord_overall]}")
    print(f"     -> all >= -0.20 (v2 not significantly worse)? "
          f"{all(d >= -0.2 for d in concord_overall)}")
    print(f"     -> sign agreement (all same direction)? "
          f"{all(d >= 0 for d in concord_overall) or all(d <= 0 for d in concord_overall)}")
    print(f"  conciseness delta (v2-v1) across judges: {[f'{d:+.2f}' for d in concord_concise]}")
    print(f"     -> all judges rate v2 at least as concise as v1? "
          f"{all(d >= 0 for d in concord_concise)}")
    print(f"     -> majority rate v2 strictly more concise? "
          f"{sum(d > 0 for d in concord_concise)}/{len(concord_concise)}")

    (BENCH / "results" / "cross_judge.json").write_text(json.dumps(summary, indent=2))
    print(f"\nWrote {BENCH / 'results' / 'cross_judge.json'}")


if __name__ == "__main__":
    main()
