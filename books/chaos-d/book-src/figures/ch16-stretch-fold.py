"""Stretch-and-fold schematic: two near points pulled apart, then folded back."""
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrow, Rectangle

OUT = Path(__file__).resolve().parent / "out"; OUT.mkdir(exist_ok=True)
BG, INK, A, B = "#fdfcf9", "#16324f", "#2b5b84", "#c0532b"

fig, ax = plt.subplots(figsize=(7.2, 4.6))
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)

def bar(y, x0, x1, label):
    ax.add_patch(Rectangle((x0, y), x1 - x0, 0.18, fc="#e9e3d6", ec=INK, lw=1.2))
    ax.text(x0 - 0.05, y + 0.09, label, ha="right", va="center", color=INK, fontsize=9)

# stage 0: original unit strip, two close dots
bar(2.4, 0.0, 1.0, "start")
ax.plot([0.30, 0.34], [2.49, 2.49], "o", color=A, ms=6)
ax.plot(0.34, 2.49, "o", color=B, ms=6)

# stage 1: stretched to 2x
bar(1.5, 0.0, 2.0, "stretch ×2")
ax.plot(0.60, 1.59, "o", color=A, ms=6)
ax.plot(0.68, 1.59, "o", color=B, ms=6)
ax.annotate("", xy=(2.0, 1.59), xytext=(1.0, 1.59),
            arrowprops=dict(arrowstyle="->", color=INK, lw=1.2))

# stage 2: folded back into the unit width
bar(0.6, 0.0, 1.0, "fold back")
ax.plot(0.60, 0.69, "o", color=A, ms=6)      # near right
ax.plot(0.32, 0.69, "o", color=B, ms=6)      # folded over -> far apart
ax.annotate("now far apart", xy=(0.46, 0.69), xytext=(1.25, 0.69),
            color=INK, fontsize=9, va="center",
            arrowprops=dict(arrowstyle="->", color=INK, lw=1))

ax.text(1.05, 2.49, "two points a hair apart", color=INK, fontsize=9, va="center")
ax.set_title("Stretch makes sensitivity; fold keeps it bounded — chaos needs both",
             color=INK, fontsize=11)
ax.set_xlim(-0.7, 2.6); ax.set_ylim(0.3, 2.95); ax.axis("off")
fig.tight_layout()
fig.savefig(OUT / "ch16-stretch-fold.svg", facecolor=BG, bbox_inches="tight")
print("ok ch16-stretch-fold")
