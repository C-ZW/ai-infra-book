# ch09 figure: determinant as signed area. Left: unit square -> parallelogram
# under spine S=[[2,1],[1,2]], shaded area=det S=3. Right: a reflection flips
# orientation, det=-1 (the corner-walk order reverses), shown by a CW arrow.
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch09-determinant-area.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

S = np.array([[2.0, 1.0], [1.0, 2.0]])          # spine: det = 2*2 - 1*1 = 3
F = np.array([[1.0, 0.0], [0.0, -1.0]])         # reflection: det = -1 (flips)
unit = np.array([[0, 1, 1, 0, 0], [0, 0, 1, 1, 0]])      # unit square, CCW corners

fig, (axL, axR) = plt.subplots(1, 2, figsize=(10, 5))
for ax, M, title, col in [(axL, S, "S=[[2,1],[1,2]]  det=+3  (no flip)", "#e07b39"),
                          (axR, F, "reflect [[1,0],[0,-1]]  det=-1  (flip)", "#7b5ea7")]:
    for k in np.arange(-3, 5):                   # faint transformed grid lines
        p = M @ np.array([[k, k], [-3, 4]]); q = M @ np.array([[-3, 4], [k, k]])
        ax.plot(p[0], p[1], color="0.85", lw=0.7); ax.plot(q[0], q[1], color="0.85", lw=0.7)
    img = M @ unit                               # image of the unit square
    ax.fill(img[0], img[1], color=col + "33", edgecolor=col, lw=1.8)
    e1, e2 = M @ np.array([1.0, 0.0]), M @ np.array([0.0, 1.0])   # columns of M
    ax.annotate("", xy=e1, xytext=(0, 0), arrowprops=dict(color="#c0392b", width=2, headwidth=9))
    ax.annotate("", xy=e2, xytext=(0, 0), arrowprops=dict(color="#2471a3", width=2, headwidth=9))
    cen = img[:, :4].mean(axis=1)                # label |det| inside the image
    ax.text(cen[0], cen[1], f"area={abs(round(np.linalg.det(M)))}", ha="center", fontsize=11, color=col)
    ax.set_title(title, fontsize=10); ax.set_xlim(-3, 4); ax.set_ylim(-3, 4); ax.set_aspect("equal")
    ax.axhline(0, color="0.4", lw=0.6); ax.axvline(0, color="0.4", lw=0.6)
    ax.set_xticks([]); ax.set_yticks([])

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
