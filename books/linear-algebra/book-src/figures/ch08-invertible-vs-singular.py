# ch08 figure: invertible vs singular -- left, spine S maps the unit grid to a
# skewed grid with nonzero area (reversible); right, a singular matrix crushes
# the whole plane onto the single line y=2x (area 0, information lost forever).
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch08-invertible-vs-singular.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

S = np.array([[2.0, 1.0], [1.0, 2.0]])             # spine S: invertible, det=3
G = np.array([[1.0, 2.0], [2.0, 4.0]])             # singular: det=0, col2=2*col1
sq = np.array([[0, 1, 1, 0, 0], [0, 0, 1, 1, 0]])  # unit square outline
lo, hi = -3, 3
lines = np.arange(lo, hi + 1)

def draw(ax, M, title, det):
    for k in lines:                                # transformed grid lines
        p = M @ np.array([[k, k], [lo, hi]]); q = M @ np.array([[lo, hi], [k, k]])
        ax.plot(p[0], p[1], color="0.82", lw=0.7); ax.plot(q[0], q[1], color="0.82", lw=0.7)
    g = M @ sq
    ax.fill(g[0], g[1], color="#f4a26155", edgecolor="#e07b39", lw=2.0)
    e1, e2 = M @ np.array([1.0, 0.0]), M @ np.array([0.0, 1.0])
    ax.annotate("", xy=e1, xytext=(0, 0), arrowprops=dict(color="#c0392b", width=2, headwidth=9))
    ax.annotate("", xy=e2, xytext=(0, 0), arrowprops=dict(color="#2471a3", width=2, headwidth=9))
    ax.set_title(f"{title}   (area = det = {det})", fontsize=10)
    ax.set_xlim(-1, 5); ax.set_ylim(-1, 5); ax.set_aspect("equal")
    ax.axhline(0, color="0.4", lw=0.6); ax.axvline(0, color="0.4", lw=0.6)

fig, axes = plt.subplots(1, 2, figsize=(11, 5.4))
draw(axes[0], S, "invertible  S=[[2,1],[1,2]]", 3)
draw(axes[1], G, "singular  [[1,2],[2,4]]  -> line y=2x", 0)
fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
