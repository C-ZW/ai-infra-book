# ch09 figure: probability of a shared birthday vs. number of people.
#
# Base numbers (must match _meta/running-examples.md verbatim):
#   B6 = 23 (people), B7 = 50.73% (probability of a match at n=23).
# Also marks n=57 (~99%, per landscape-history.md) as the "near certain" point.
#
# All in-image text is English/numbers only: matplotlib on this machine has no
# bundled CJK glyphs, so Chinese text renders as tofu boxes. The Traditional
# Chinese caption lives in the chapter markdown's ![...] alt text instead.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch09-birthday-curve.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

DAYS = 365


def p_match(n, days=DAYS):
    p_no_match = 1.0
    for i in range(n):
        p_no_match *= (days - i) / days
    return 1 - p_no_match


ns = list(range(1, 81))
ps = [p_match(n) * 100 for n in ns]

fig, ax = plt.subplots(figsize=(7.5, 5.2))
ax.plot(ns, ps, color="#1f5fa8", linewidth=2.2)
ax.axhline(50, color="#999999", linewidth=0.8, linestyle="--")
ax.axhline(99, color="#999999", linewidth=0.8, linestyle="--")

p23 = p_match(23) * 100
ax.plot([23], [p23], marker="o", color="#c0392b", markersize=7, zorder=5)
ax.annotate(f"n=23 -> {p23:.2f}%\n(just over half)",
            xy=(23, p23), xytext=(28, 60),
            arrowprops=dict(arrowstyle="->", color="#c0392b"),
            fontsize=10, color="#c0392b")

p57 = p_match(57) * 100
ax.plot([57], [p57], marker="o", color="#1e7d32", markersize=7, zorder=5)
ax.annotate(f"n=57 -> {p57:.2f}%\n(nearly certain)",
            xy=(57, p57), xytext=(42, 78),
            arrowprops=dict(arrowstyle="->", color="#1e7d32"),
            fontsize=10, color="#1e7d32")

ax.set_xlabel("number of people in the room (n)")
ax.set_ylabel("P(at least one shared birthday), %")
ax.set_title("Birthday-match probability climbs far faster than people count")
ax.set_xlim(0, 80)
ax.set_ylim(0, 105)
ax.grid(True, alpha=0.25)

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
