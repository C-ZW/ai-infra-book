# ch22 figure: the Newcomb payoff matrix, with two arrows showing how
# causal decision theory (CDT) and evidential decision theory (EDT) each
# read the same table in a different direction.
#
# Rows = your act (one-box / two-box). Columns = predictor's prediction
# (predicted one-box / predicted two-box). CDT compares within each column
# (row-wise dominance: two-box always +$1,000). EDT compares along the
# diagonal (the predictor tracks your actual act, so the realized outcome
# is almost always top-left or bottom-right).
#
# All in-image text is English/numbers only (this machine has no bundled
# CJK glyphs); the Traditional Chinese caption lives in the chapter's
# markdown alt text instead.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

OUT = Path(__file__).resolve().parent / "out" / "ch22-newcomb-matrix.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(8.6, 6.0))

# grid geometry
x0, y0, w, h = 2.6, 1.2, 3.0, 1.6
cells = {
    "one_pred_one": (x0, y0 + h, "$1,000,000"),
    "one_pred_two": (x0 + w, y0 + h, "$0"),
    "two_pred_one": (x0, y0, "$1,001,000"),
    "two_pred_two": (x0 + w, y0, "$1,000"),
}
for key, (x, y, label) in cells.items():
    ax.add_patch(Rectangle((x, y), w, h, facecolor="#f7f7f2", edgecolor="black", linewidth=1.6))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=15, weight="bold")

# row / column labels
ax.text(x0 - 0.15, y0 + h + h / 2, "You: one-box\n(take only B)", ha="right", va="center", fontsize=11)
ax.text(x0 - 0.15, y0 + h / 2, "You: two-box\n(take A and B)", ha="right", va="center", fontsize=11)
ax.text(x0 + w / 2, y0 + 2 * h + 0.35, "Predicted: one-box", ha="center", fontsize=11)
ax.text(x0 + w + w / 2, y0 + 2 * h + 0.35, "Predicted: two-box", ha="center", fontsize=11)

# CDT arrow: vertical, compares within each column (row-wise dominance)
for cx in (x0 + w / 2, x0 + w + w / 2):
    arrow = FancyArrowPatch((cx, y0 + h + h - 0.15), (cx, y0 + 0.15),
                             arrowstyle="-|>", mutation_scale=20,
                             color="#8a1f1f", linewidth=2.2, linestyle="--")
    ax.add_patch(arrow)
ax.text(x0 + w, y0 - 0.55, "CDT: compare down each column -> two-box wins by $1,000 either way",
        ha="center", fontsize=10.5, color="#8a1f1f")

# EDT arrow: diagonal, compares the two "predictor got it right" cells
diag = FancyArrowPatch((x0 + 0.25, y0 + h + h - 0.25), (x0 + w + 0.25, y0 + 0.25),
                        connectionstyle="arc3,rad=-0.25", arrowstyle="-|>",
                        mutation_scale=20, color="#1a3a6b", linewidth=2.2)
ax.add_patch(diag)
ax.text(x0 + w / 2 + 0.1, y0 + h + 0.35,
        "EDT: reliable predictor -> real outcomes cluster on this diagonal",
        ha="center", fontsize=10.5, color="#1a3a6b")

ax.set_xlim(0, x0 + 2 * w + 0.4)
ax.set_ylim(0, y0 + 2 * h + 0.9)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("Newcomb's payoff matrix: two rules read it two ways", fontsize=13)

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
