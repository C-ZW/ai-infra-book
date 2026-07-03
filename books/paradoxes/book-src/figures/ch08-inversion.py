# ch08 figure: schematic of the conditional-inversion direction reversal.
#
# The chapter's whole point: P(E|H) (measured by the expert) and P(H|E)
# (wanted by the court) point in opposite directions between the same two
# nodes, H = "innocent" and E = "the evidence observed". They are only
# equal to each other by coincidence; bridging one to the other requires
# multiplying by a prior P(H) that courtroom rhetoric usually never states.
#
# All in-image text is English/numbers only: matplotlib on this machine has no
# bundled CJK glyphs, so Chinese text renders as tofu boxes. The Traditional
# Chinese caption lives in the chapter markdown's ![...] alt text instead.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle

OUT = Path(__file__).resolve().parent / "out" / "ch08-inversion.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(8.4, 5.2))

H, E = (1.6, 2.5), (6.8, 2.5)
ax.add_patch(Circle(H, 0.95, facecolor="#dbe4f0", edgecolor="#1a3a6b", linewidth=2, zorder=3))
ax.add_patch(Circle(E, 0.95, facecolor="#f0dbdb", edgecolor="#8a1f1f", linewidth=2, zorder=3))
ax.text(*H, "H\ninnocent", ha="center", va="center", fontsize=13, weight="bold", zorder=4)
ax.text(*E, "E\nthe evidence", ha="center", va="center", fontsize=13, weight="bold", zorder=4)

# top arrow: H -> E, the quantity the expert actually measured
top = FancyArrowPatch((H[0] + 0.75, H[1] + 0.65), (E[0] - 0.75, E[1] + 0.65),
                       connectionstyle="arc3,rad=0.30", arrowstyle="-|>",
                       mutation_scale=22, color="#1a3a6b", linewidth=2.2)
ax.add_patch(top)
ax.text(4.2, 4.15, "P(E | H)  --  measured by the expert\ne.g. 1 in 73,000,000",
        ha="center", fontsize=11, color="#1a3a6b")

# bottom arrow: E -> H, the quantity the court actually wants
bottom = FancyArrowPatch((E[0] - 0.75, E[1] - 0.65), (H[0] + 0.75, H[1] - 0.65),
                          connectionstyle="arc3,rad=0.30", arrowstyle="-|>",
                          mutation_scale=22, color="#8a1f1f", linewidth=2.2)
ax.add_patch(bottom)
ax.text(4.2, 0.75, "P(H | E)  --  wanted by the court\nneeds a prior P(H), rarely stated aloud",
        ha="center", fontsize=11, color="#8a1f1f")

ax.text(4.2, 2.5, "NOT\nequal", ha="center", va="center", fontsize=12,
        style="italic", color="#333333")

ax.set_xlim(0, 8.4)
ax.set_ylim(0, 5.2)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("Two directions of the same conditional probability", fontsize=13)

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
