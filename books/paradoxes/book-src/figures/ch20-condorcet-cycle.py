# ch20 figure: Condorcet paradox -- pairwise-majority cycle.
#
# Three voters, three alternatives (A, B, C). Pairwise majority vote gives
# A beats B (2:1), B beats C (2:1), C beats A (2:1) -- a closed cycle with
# no Condorcet winner. Arrows point from the pairwise winner to the option
# it beats. All in-image text is English/numbers only: this machine's
# matplotlib has no bundled CJK glyphs. The Traditional Chinese caption
# lives in the chapter markdown's ![...] alt text.
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle

OUT = Path(__file__).resolve().parent / "out" / "ch20-condorcet-cycle.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(6.4, 6.4))

pos = {
    "A": np.array([0.0, 1.0]),
    "B": np.array([-0.87, -0.5]),
    "C": np.array([0.87, -0.5]),
}
colors = {"A": "#1565c0", "B": "#2e7d32", "C": "#c62828"}

for name, p in pos.items():
    ax.add_patch(Circle(p, 0.22, facecolor=colors[name], edgecolor="black",
                         zorder=3))
    ax.text(*p, name, ha="center", va="center", color="white",
            fontsize=20, fontweight="bold", zorder=4)

edges = [("A", "B"), ("B", "C"), ("C", "A")]
for src, dst in edges:
    p0, p1 = pos[src], pos[dst]
    arrow = FancyArrowPatch(p0, p1, connectionstyle="arc3,rad=0.25",
                             arrowstyle="-|>", mutation_scale=22,
                             linewidth=2.4, color="black", zorder=2,
                             shrinkA=24, shrinkB=24)
    ax.add_patch(arrow)
    mid = (p0 + p1) / 2
    normal = np.array([-(p1 - p0)[1], (p1 - p0)[0]])
    normal = normal / np.linalg.norm(normal) * 0.34
    lp = mid + normal
    ax.text(*lp, f"{src} beats {dst}\n(2 : 1 voters)", ha="center",
            va="center", fontsize=10)

ax.set_xlim(-1.6, 1.6)
ax.set_ylim(-1.4, 1.6)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("Condorcet paradox: the majority-rule cycle\n"
              "A beats B, B beats C, C beats A -- no Condorcet winner",
              fontsize=12)
fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
