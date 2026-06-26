# ch06 figure: order matters -- shear-then-rotate vs rotate-then-shear give different end states
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch06-composition-order.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

H = np.array([[1.0, 1.0], [0.0, 1.0]])              # shear
R = np.array([[0.0, -1.0], [1.0, 0.0]])            # rotate 90 deg CCW
sq = np.array([[0, 1, 1, 0, 0], [0, 0, 1, 1, 0]])  # unit square
e1 = np.array([1.0, 0.0])

def draw(ax, M, title):
    g = M @ sq
    ax.fill(g[0], g[1], color="#f4a26133", edgecolor="#e07b39", lw=1.8)
    v = M @ e1                                      # track e1 = (1,0)
    ax.annotate("", xy=v, xytext=(0, 0), arrowprops=dict(color="#c0392b", width=2, headwidth=9))
    ax.text(v[0] + 0.08, v[1] + 0.08, f"({v[0]:.0f},{v[1]:.0f})", color="#c0392b", fontsize=9)
    ax.set_title(title, fontsize=10); ax.set_xlim(-2.2, 2.4); ax.set_ylim(-0.6, 2.4)
    ax.set_aspect("equal"); ax.axhline(0, color="0.6", lw=0.6); ax.axvline(0, color="0.6", lw=0.6)

fig, axs = plt.subplots(2, 3, figsize=(10.5, 7))
draw(axs[0, 0], np.eye(2), "start: unit square")           # top row: shear then rotate
draw(axs[0, 1], H, "after H (shear)")
draw(axs[0, 2], R @ H, "then R:  RH = [[0,-1],[1,1]]")
draw(axs[1, 0], np.eye(2), "start: unit square")           # bottom row: rotate then shear
draw(axs[1, 1], R, "after R (rotate 90)")
draw(axs[1, 2], H @ R, "then H:  HR = [[1,-1],[1,0]]")
fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
