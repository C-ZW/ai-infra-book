# ch01 figure: the spine matrix S=[[2,1],[1,2]] acting on the grid (before vs after)
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch01-grid-to-S.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

S = np.array([[2.0, 1.0], [1.0, 2.0]])
lo, hi = -3, 4
lines = np.arange(lo, hi + 1)

fig, (axL, axR) = plt.subplots(1, 2, figsize=(9, 4.6))
for ax, M, title in [(axL, np.eye(2), "before:  identity grid"),
                     (axR, S, "after:  S = [[2,1],[1,2]]")]:
    for k in lines:                                  # draw the (transformed) grid lines
        p = M @ np.array([[k, k], [lo, hi]]); q = M @ np.array([[lo, hi], [k, k]])
        ax.plot(p[0], p[1], color="0.8", lw=0.8); ax.plot(q[0], q[1], color="0.8", lw=0.8)
    sq = M @ np.array([[0, 1, 1, 0, 0], [0, 0, 1, 1, 0]])   # unit square -> image
    ax.fill(sq[0], sq[1], color="#f4a26122", edgecolor="#e07b39", lw=1.6)
    e1, e2 = M @ np.array([1, 0]), M @ np.array([0, 1])      # basis vectors go to S columns
    ax.annotate("", xy=e1, xytext=(0, 0), arrowprops=dict(color="#c0392b", width=2, headwidth=9))
    ax.annotate("", xy=e2, xytext=(0, 0), arrowprops=dict(color="#2471a3", width=2, headwidth=9))
    ax.text(*(e1 + (0.12, -0.28)), "e1", color="#c0392b"); ax.text(*(e2 + (-0.45, 0.1)), "e2", color="#2471a3")
    ax.set_title(title); ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
    ax.axhline(0, color="0.4", lw=0.6); ax.axvline(0, color="0.4", lw=0.6)
axR.text(3.05, 3.05, "(3,3)  area=3", fontsize=8, color="#e07b39")

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
