# ch06 figure: natural-frequency icon grid, true positives vs false positives.
#
# Base numbers (must match _meta/running-examples.md verbatim):
#   B3 prevalence = 1/1000, B4 sensitivity = specificity = 99%, B5 posterior ~= 9.02%.
# Among 100,000 people: 100 diseased (99 true positive + 1 false negative),
# 99,900 healthy (999 false positive + 98,901 true negative).
# This figure only draws the "tested positive" subset (99 + 999 = 1098 icons):
# one icon = one person. The area contrast between the small green block and
# the much larger red block IS the 9.02% answer, made visible.
#
# All in-image text is English/numbers only: matplotlib on this machine has no
# bundled CJK glyphs, so Chinese text renders as tofu boxes. The Traditional
# Chinese caption lives in the chapter markdown's ![...] alt text instead.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

OUT = Path(__file__).resolve().parent / "out" / "ch06-frequency-grid.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

TP, FP = 99, 999                 # out of 100,000 people who test positive
TOTAL = TP + FP                  # 1098
NCOLS = 34
NROWS = -(-TOTAL // NCOLS)       # ceil division -> 33 rows (1122 cells, 24 left blank)

fig, ax = plt.subplots(figsize=(7.4, 6.6))
for i in range(TOTAL):
    row, col = divmod(i, NCOLS)
    color = "#1e7d32" if i < TP else "#b71c1c"   # first TP cells green, rest FP red
    ax.add_patch(mpatches.Rectangle((col, NROWS - 1 - row), 0.86, 0.86,
                                     facecolor=color, edgecolor="none"))

ax.set_xlim(0, NCOLS)
ax.set_ylim(-2.6, NROWS)
ax.set_aspect("equal")
ax.axis("off")

posterior = TP / TOTAL
ax.set_title(
    "Everyone who tests positive, out of 100,000 people screened\n"
    f"green = {TP} true positives     red = {FP} false positives",
    fontsize=12,
)
ax.text(NCOLS / 2, -1.6,
        f"P(disease | positive) = {TP}/{TOTAL} = {posterior*100:.2f}%",
        ha="center", va="center", fontsize=13, weight="bold")

legend = [
    mpatches.Patch(facecolor="#1e7d32", label=f"true positive  n={TP}"),
    mpatches.Patch(facecolor="#b71c1c", label=f"false positive  n={FP}"),
]
ax.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, 0.02),
          ncol=2, frameon=False, fontsize=10)

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
