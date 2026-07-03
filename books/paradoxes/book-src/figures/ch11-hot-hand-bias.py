# ch11 figure: the Miller-Sanjurjo (2018) finite-sample selection bias.
# For a fair coin sequence, look only at flips that immediately follow two
# consecutive heads (HH), and compute the fraction of those that are also
# H. Average this fraction across sequences where it is defined (sequences
# with zero HH-opportunities are dropped -- that drop is exactly where the
# bias sneaks in). Every flip is truly independent (P(H)=0.5 always, no
# memory), yet this statistic sits below 0.5 for short sequences and only
# approaches 0.5 as sequence length grows.
from pathlib import Path
from itertools import product
import random
import matplotlib
matplotlib.use("Agg")  # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch11-hot-hand-bias.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)


def streak_rate(seq):
    hits = opportunities = 0
    for i in range(2, len(seq)):
        if seq[i - 2] == 1 and seq[i - 1] == 1:
            opportunities += 1
            if seq[i] == 1:
                hits += 1
    return hits, opportunities


def exact_expectation(n):
    total, count = 0.0, 0
    for seq in product([0, 1], repeat=n):
        hits, opp = streak_rate(seq)
        if opp > 0:
            total += hits / opp
            count += 1
    return total / count


def monte_carlo_expectation(n, trials=300_000, seed=0):
    rng = random.Random(seed)
    total, count = 0.0, 0
    for _ in range(trials):
        seq = [rng.randint(0, 1) for _ in range(n)]
        hits, opp = streak_rate(seq)
        if opp > 0:
            total += hits / opp
            count += 1
    return total / count


exact_ns = [4, 6, 8, 10, 12, 14, 16, 18]
exact_vals = [exact_expectation(n) for n in exact_ns]

mc_ns = [20, 30, 50, 80, 120]
mc_vals = [monte_carlo_expectation(n) for n in mc_ns]

fig, ax = plt.subplots(figsize=(7.2, 4.6))
ax.plot(exact_ns, exact_vals, "o-", color="#d9483d", label="exact enumeration (2^n sequences)")
ax.plot(mc_ns, mc_vals, "s--", color="#2a6f97", label="Monte Carlo estimate (300,000 trials)")
ax.axhline(0.5, color="black", linewidth=1, linestyle=":")
ax.text(120, 0.508, "true value = 0.5 (real independence)", fontsize=8, ha="right")
ax.set_xlabel("sequence length n (fair coin flips)")
ax.set_ylabel("E[ hit rate following HH | at least one HH occurs ]")
ax.set_title("Short sequences under-count 0.5 even when every flip is independent")
ax.legend(fontsize=8, loc="lower right")
ax.set_ylim(0.35, 0.52)
fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
