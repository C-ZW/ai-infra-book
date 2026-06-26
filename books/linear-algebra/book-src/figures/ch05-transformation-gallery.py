# ch05 figure: a 2x3 gallery of 2D linear transformations; each panel shows the
# grid deformed and where the basis vectors e1, e2 land (the matrix columns).
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch05-transformation-gallery.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

c = np.cos(np.pi / 2); s = np.sin(np.pi / 2)          # 90 degrees, counterclockwise
gallery = [("scale [[2,0],[0,2]]", [[2, 0], [0, 2]]),
           ("shear [[1,1],[0,1]]", [[1, 1], [0, 1]]),
           ("rotate R(90)", [[c, -s], [s, c]]),
           ("reflect [[1,0],[0,-1]]", [[1, 0], [0, -1]]),
           ("project [[1,0],[0,0]]", [[1, 0], [0, 0]]),
           ("spine S [[2,1],[1,2]]", [[2, 1], [1, 2]])]

lo, hi = -3, 3
lines = np.arange(lo, hi + 1)
fig, axes = plt.subplots(2, 3, figsize=(11, 7.4))
for ax, (title, mat) in zip(axes.ravel(), gallery):
    M = np.array(mat, dtype=float)
    for k in lines:                                   # draw the transformed grid lines
        p = M @ np.array([[k, k], [lo, hi]]); q = M @ np.array([[lo, hi], [k, k]])
        ax.plot(p[0], p[1], color="0.82", lw=0.7); ax.plot(q[0], q[1], color="0.82", lw=0.7)
    e1, e2 = M @ np.array([1.0, 0.0]), M @ np.array([0.0, 1.0])   # basis vectors -> columns
    ax.annotate("", xy=e1, xytext=(0, 0), arrowprops=dict(color="#c0392b", width=2, headwidth=9))
    ax.annotate("", xy=e2, xytext=(0, 0), arrowprops=dict(color="#2471a3", width=2, headwidth=9))
    ax.text(e1[0] + 0.1, e1[1] - 0.1, f"e1->{tuple(int(x) for x in e1)}", color="#c0392b", fontsize=7)
    ax.text(e2[0] - 0.1, e2[1] + 0.15, f"e2->{tuple(int(x) for x in e2)}", color="#2471a3", fontsize=7)
    ax.set_title(title, fontsize=9); ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
    ax.axhline(0, color="0.4", lw=0.6); ax.axvline(0, color="0.4", lw=0.6)
    ax.set_xticks([]); ax.set_yticks([])

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)             # build_figures.py reads this
