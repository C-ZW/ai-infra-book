"""ch18: The impossibility reduction chain for the Two Generals' Problem.

Draws four rows, one per candidate protocol length k = 3, 2, 1, 0. Each row
shows k message arrows shuttling between General A (left) and General B
(right); the last arrow in each row is dashed and red -- it may always be
lost, and its sender can never confirm delivery. A vertical arrow between
rows marks that this unconfirmable last message can always be dropped,
so the same guarantee would have to hold one level down. Recursing to
k = 0 (no messages at all) still has to guarantee a coordinated attack,
which is absurd -- the contradiction at the heart of the impossibility
proof. Labels are kept in English; the Chinese narrative sits in the text.

Output: figures/out/ch18-two-generals.svg
"""
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(9.5, 7.6))
ax.axis("off")
ax.set_xlim(0, 10.2)
ax.set_ylim(-0.6, 9.6)

xA, xB = 3.1, 8.6
ax.text(xA, 9.15, "General A", ha="center", fontsize=11, fontweight="bold")
ax.text(xB, 9.15, "General B", ha="center", fontsize=11, fontweight="bold")

rows_y = [7.6, 5.4, 3.2, 1.0]
levels = [3, 2, 1, 0]
for idx, (k, y) in enumerate(zip(levels, rows_y)):
    ax.text(0.25, y, f"k={k}", fontsize=13, fontweight="bold", va="center")
    if k == 0:
        ax.add_patch(plt.Rectangle((xA - 0.9, y - 0.42), xB - xA + 1.8, 0.84,
                                    facecolor="#c0392b1a", edgecolor="#c0392b", linewidth=1.6))
        ax.text((xA + xB) / 2, y, "0 messages -- still must guarantee a\nsimultaneous attack: contradiction",
                ha="center", va="center", fontsize=9.3, color="#c0392b")
    else:
        seg = (xB - xA) / k
        for i in range(k):
            x1, x2 = xA + seg * i, xA + seg * (i + 1)
            src, dst = (x1, x2) if i % 2 == 0 else (x2, x1)
            last = i == k - 1
            style = dict(arrowstyle="-|>", mutation_scale=15,
                         color="#c0392b" if last else "0.3", linewidth=1.6,
                         linestyle="--" if last else "-")
            ax.annotate("", xy=(dst, y), xytext=(src, y), arrowprops=style)
        ax.text(xB + 0.2, y, "last msg\nmay be lost", fontsize=8, color="#c0392b", va="center")
    if idx < len(levels) - 1:
        ax.annotate("", xy=(xA - 0.45, rows_y[idx + 1] + 0.55), xytext=(xA - 0.45, y - 0.4),
                    arrowprops=dict(arrowstyle="-|>", color="0.35", linewidth=1.4))
        ax.text(xA - 0.6, (y + rows_y[idx + 1]) / 2, "drop it --\nsender can't\nconfirm delivery",
                fontsize=7.3, ha="right", va="center", color="0.3")

ax.set_title("Two Generals: the last message is always removable, down to zero -- a contradiction",
              fontsize=11.5, pad=10)
fig.tight_layout()

out_path = Path(__file__).resolve().parent / "out" / "ch18-two-generals.svg"
out_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out_path, format="svg")
print(f"Saved: {out_path}")
