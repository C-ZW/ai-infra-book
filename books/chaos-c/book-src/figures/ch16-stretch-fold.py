"""Schematic of stretch-and-fold: the engine of chaos."""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mp
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

fig, ax = plt.subplots(figsize=(8.6, 3.4))
ax.axis("off")
ax.set_xlim(0, 10)
ax.set_ylim(0, 3.2)

# stage 1: a square with two nearby dots
ax.add_patch(mp.Rectangle((0.2, 1.0), 1.4, 1.4, fill=True,
             facecolor="#cfe2f3", edgecolor="#1f4e79"))
ax.plot([0.6, 0.75], [1.6, 1.6], "o", ms=4, color="#c00000")
ax.text(0.9, 0.6, "start", ha="center", fontsize=9)

ax.annotate("", xy=(3.4, 1.7), xytext=(1.9, 1.7),
            arrowprops=dict(arrowstyle="->", lw=1.4))
ax.text(2.65, 2.0, "stretch", ha="center", fontsize=9, color="#1f4e79")

# stage 2: stretched rectangle, dots now far apart
ax.add_patch(mp.Rectangle((3.6, 1.3), 3.0, 0.7, fill=True,
             facecolor="#cfe2f3", edgecolor="#1f4e79"))
ax.plot([3.9, 4.5], [1.65, 1.65], "o", ms=4, color="#c00000")
ax.text(5.1, 0.9, "pulled apart (x2)", ha="center", fontsize=9)

ax.annotate("", xy=(8.0, 1.7), xytext=(6.8, 1.7),
            arrowprops=dict(arrowstyle="->", lw=1.4))
ax.text(7.4, 2.0, "fold", ha="center", fontsize=9, color="#1f4e79")

# stage 3: folded horseshoe back inside original footprint
theta = np.linspace(-np.pi / 2, np.pi / 2, 60)
cx, cy, rO, rI = 8.9, 1.7, 0.85, 0.5
xo = cx + rO * np.cos(theta)
yo = cy + rO * np.sin(theta)
xi = cx + rI * np.cos(theta[::-1])
yi = cy + rI * np.sin(theta[::-1])
xs = np.concatenate([xo, [cx, cx], xi, [cx, cx]])
ys = np.concatenate([yo, [cy + rO, cy + rO], yi, [cy - rO, cy - rO]])
ax.fill(np.concatenate([xo, xi]), np.concatenate([yo, yi]),
        facecolor="#cfe2f3", edgecolor="#1f4e79")
ax.text(8.9, 0.45, "folded back inside", ha="center", fontsize=9)

ax.set_title("Stretch makes sensitivity; fold keeps it bounded", fontsize=11)
fig.tight_layout()
fig.savefig(OUT / "ch16-stretch-fold.svg")
print("wrote ch16-stretch-fold.svg")
