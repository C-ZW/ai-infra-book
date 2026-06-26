# ch04 figure: same vector v read in two grids -- standard grid vs the skew eigenbasis grid
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch04-change-of-basis.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

b1, b2 = np.array([1.0, 1.0]), np.array([1.0, -1.0])   # eigenbasis of S
v = np.array([3.0, 3.0])                               # standard coords (3,3) = 3*b1 + 0*b2

fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 5.4))
rng = range(-4, 5)

# LEFT: standard grid; v reads (3, 3)
for k in rng:
    axL.axhline(k, color="0.85", lw=0.8); axL.axvline(k, color="0.85", lw=0.8)
axL.arrow(0, 0, 1, 0, color="C0", width=0.05, length_includes_head=True)  # e1
axL.arrow(0, 0, 0, 1, color="C2", width=0.05, length_includes_head=True)  # e2
axL.arrow(0, 0, v[0], v[1], color="C3", width=0.06, length_includes_head=True)
axL.text(v[0] + 0.2, v[1], "v reads (3, 3)", color="C3", fontsize=10)
axL.set_title("standard grid: coords = (3, 3)")

# RIGHT: skew grid spanned by b1,b2; same v reads (3, 0)
for k in rng:                                          # lines along b1 (shifted by k*b2) and vice versa
    p = k * b2; axR.plot([p[0] - 5*b1[0], p[0] + 5*b1[0]], [p[1] - 5*b1[1], p[1] + 5*b1[1]], color="0.85", lw=0.8)
    p = k * b1; axR.plot([p[0] - 5*b2[0], p[0] + 5*b2[0]], [p[1] - 5*b2[1], p[1] + 5*b2[1]], color="0.85", lw=0.8)
axR.arrow(0, 0, b1[0], b1[1], color="C0", width=0.05, length_includes_head=True)  # b1=(1,1)
axR.arrow(0, 0, b2[0], b2[1], color="C2", width=0.05, length_includes_head=True)  # b2=(1,-1)
axR.arrow(0, 0, v[0], v[1], color="C3", width=0.06, length_includes_head=True)
axR.text(v[0] + 0.2, v[1], "v reads (3, 0)", color="C3", fontsize=10)
axR.set_title("eigenbasis grid {(1,1),(1,-1)}: coords = (3, 0)")

for ax in (axL, axR):
    ax.set_aspect("equal"); ax.set_xlim(-4.2, 4.5); ax.set_ylim(-4.2, 4.5)
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
