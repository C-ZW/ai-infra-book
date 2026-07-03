# ch12 figure: partial sums of the St. Petersburg series under two "prices".
#
# Base number (must match _meta/running-examples.md verbatim):
#   B10: expected payout = Sum(n=1..inf) 2^n * (1/2^n) = Sum 1 = infinity.
# Left panel: the raw-money partial sum S_N = sum_{n=1}^N 1 = N. It is a
# straight, unbounded line -- every extra term adds exactly 1 more ducat of
# expectation, forever. There is no ceiling.
# Right panel: run the SAME game through Daniel Bernoulli's log-utility lens.
# Partial sum of (1/2^n)*ln(2^n) converges (n/2^n is summable), so its
# certainty-equivalent CE_N = exp(partial sum) saturates near 4 ducats by
# about N=15. Same diverging series, but weighted by log utility instead of
# raw money, it stops climbing. That contrast IS the paradox's resolution.
#
# All in-image text is English/numbers only: matplotlib on this machine has no
# bundled CJK glyphs, so Chinese text renders as tofu boxes. The Traditional
# Chinese caption lives in the chapter markdown's ![...] alt text instead.
from pathlib import Path
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch12-stpetersburg.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

N_MAX = 22
ns = list(range(1, N_MAX + 1))

# Left: raw expectation partial sum, S_N = N ducats.
money_partial = ns  # S_N = N exactly, per term contributes 2^n * (1/2^n) = 1

# Right: log-utility partial sum, exponentiated back into ducats (w=0 baseline).
util_running = 0.0
ce = []
for n in ns:
    util_running += (2.0 ** -n) * math.log(2.0 ** n)
    ce.append(math.exp(util_running))

fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.2))

ax = axes[0]
ax.plot(ns, money_partial, marker="o", markersize=3, color="#b71c1c")
ax.set_title("Expected payout, partial sum S_N = N\n(no ceiling, ever)")
ax.set_xlabel("terms included (N)")
ax.set_ylabel("ducats")
ax.grid(alpha=0.3)

ax = axes[1]
ax.plot(ns, ce, marker="o", markersize=3, color="#1e7d32")
ax.axhline(4.0, color="gray", linestyle="--", linewidth=1)
ax.text(N_MAX * 0.5, 4.15, "limit = 4 ducats", fontsize=9, color="gray")
ax.set_title("Same series under log utility\ncertainty-equivalent price saturates")
ax.set_xlabel("terms included (N)")
ax.set_ylabel("ducats (willing-to-pay)")
ax.set_ylim(0, 5)
ax.grid(alpha=0.3)

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
