# ch13 figure: the SAME S=[[2,1],[1,2]] in two coordinate views.
# LEFT (standard grid): a unit square gets sheared/skewed -- looks "complex".
# RIGHT (eigenbasis grid {(1,1),(1,-1)}): the same S is pure stretch -- the
# square's two eigen-axes scale by 3 and by 1, no skew. "Complexity = wrong coords."
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch13-diagonalization.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

S = np.array([[2.0, 1.0], [1.0, 2.0]])          # spine: eigvals 3 (along (1,1)) and 1 (along (1,-1))
e1, e2 = np.array([1.0, 1.0]), np.array([1.0, -1.0])  # eigen-axes (used as directions)
sq = np.array([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]).T   # unit square (closed)

fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 5.4))

# LEFT: standard coords. Unit square and its image S@square (skewed parallelogram).
for k in range(-1, 4):
    axL.axhline(k, color="0.9", lw=0.7); axL.axvline(k, color="0.9", lw=0.7)
axL.plot(sq[0], sq[1], color="0.5", lw=1.5, label="unit square")
img = S @ sq
axL.plot(img[0], img[1], color="#c0392b", lw=2.0, label="S(square): skewed")
axL.set_title("standard grid: S skews the square (looks complex)", fontsize=10)
axL.legend(loc="upper left", fontsize=8)

# RIGHT: eigenbasis coords. Square aligned to eigen-axes and its image:
# along (1,1) scale x3, along (1,-1) scale x1 -> pure stretch, no skew.
base = np.array([e1, e2]).T                      # columns are the eigen-axes
sq_eig = base @ sq                               # unit square drawn in eigen-axes
img_eig = base @ (np.diag([3.0, 1.0]) @ sq)      # same square scaled (3,1) along eigen-axes
for d, col in [(e1, "#c0392b"), (e2, "#2471a3")]:
    axR.plot([-3 * d[0], 3 * d[0]], [-3 * d[1], 3 * d[1]], color=col, lw=1.0, ls="--", alpha=0.7)
axR.plot(sq_eig[0], sq_eig[1], color="0.5", lw=1.5, label="square (eigen-axes)")
axR.plot(img_eig[0], img_eig[1], color="#c0392b", lw=2.0, label="x3 along (1,1), x1 along (1,-1)")
axR.set_title("eigenbasis grid: S = pure stretch (3 and 1), no skew", fontsize=10)
axR.legend(loc="upper left", fontsize=8)

for ax in (axL, axR):
    ax.set_aspect("equal"); ax.set_xlim(-3.2, 4.2); ax.set_ylim(-3.2, 4.2)
    ax.axhline(0, color="0.6", lw=0.6); ax.axvline(0, color="0.6", lw=0.6)
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
