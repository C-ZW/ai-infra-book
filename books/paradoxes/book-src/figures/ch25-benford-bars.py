# ch25 figure: leading-digit probability under Benford's law.
#
# Base number (must match _meta/running-examples.md verbatim):
#   B12 = 30.10% (P(first digit = 1) = log10(2)).
# Full table (must match _meta/landscape-history.md, one-decimal rounding):
#   1->30.1, 2->17.6, 3->12.5, 4->9.7, 5->7.9, 6->6.7, 7->5.8, 8->5.1, 9->4.6 (%)
#
# All in-image text is English/numbers only: matplotlib on this machine has no
# bundled CJK glyphs, so Chinese text renders as tofu boxes. The Traditional
# Chinese caption lives in the chapter markdown's ![...] alt text instead.
import math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch25-benford-bars.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

digits = list(range(1, 10))
probs = [math.log10(1 + 1 / d) * 100 for d in digits]
uniform = 100 / 9

fig, ax = plt.subplots(figsize=(7.5, 5.2))
bars = ax.bar(digits, probs, color="#1f5fa8", width=0.62, zorder=3)

ax.axhline(uniform, color="#c0392b", linewidth=1.4, linestyle="--", zorder=2,
           label=f"naive guess: uniform 1/9 = {uniform:.1f}%")

for d, p in zip(digits, probs):
    ax.text(d, p + 0.6, f"{p:.1f}%", ha="center", fontsize=9, color="#1f3b5c")

ax.annotate("P(1) = log10(2) = 30.10%",
            xy=(1, probs[0]), xytext=(3.1, 27),
            arrowprops=dict(arrowstyle="->", color="#1f5fa8"),
            fontsize=10, color="#1f5fa8")

ax.set_xlabel("leading digit d")
ax.set_ylabel("P(leading digit = d), %")
ax.set_title("Benford's law: P(d) = log10(1 + 1/d), monotonically decreasing")
ax.set_xticks(digits)
ax.set_ylim(0, 34)
ax.legend(loc="upper right", fontsize=9, frameon=False)
ax.grid(True, axis="y", alpha=0.25, zorder=0)

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
