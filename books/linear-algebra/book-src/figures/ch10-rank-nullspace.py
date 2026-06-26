# ch10 figure: projection [[1,0],[0,0]] flattens the plane onto the x-axis.
# Show the null space (whole y-axis collapses to the origin) and the column
# space (x-axis = the image). rank 1 + nullity 1 = 2.
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch10-rank-nullspace.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

P = np.array([[1.0, 0.0], [0.0, 0.0]])         # projection onto the x-axis
lo, hi = -3, 3
fig, ax = plt.subplots(figsize=(6, 6))

# faint background grid (the domain, R^2)
for k in np.arange(lo, hi + 1):
    ax.plot([lo, hi], [k, k], color="0.88", lw=0.7)
    ax.plot([k, k], [lo, hi], color="0.88", lw=0.7)

# null space = y-axis: every (0,y) is sent to the origin (0,0)
ax.plot([0, 0], [lo, hi], color="#2471a3", lw=3, label="null space (y-axis -> 0)")
for y in [1.0, 2.0, -1.0, -2.0]:                # arrows: y-axis points collapse to 0
    ax.annotate("", xy=(0, 0), xytext=(0, y),
                arrowprops=dict(color="#2471a3", lw=1.0, ls="--", arrowstyle="->"))

# column space = x-axis = image of P (everything lands here)
ax.plot([lo, hi], [0, 0], color="#c0392b", lw=3, label="column space (x-axis = image)")

# a sample point (2.4,2) projected down to (2.4,0): rank-1 image, nullity-1 drop
v = np.array([2.4, 2.0]); Pv = P @ v
ax.annotate("", xy=Pv, xytext=tuple(v), arrowprops=dict(color="#7d3c98", lw=1.6, arrowstyle="->"))
ax.plot(*v, "o", color="#7d3c98"); ax.plot(*Pv, "o", color="#c0392b")
ax.text(v[0] + 0.1, v[1], "v=(2.4,2)", color="#7d3c98", fontsize=9)
ax.text(Pv[0] + 0.1, Pv[1] - 0.28, "Pv=(2.4,0)", color="#c0392b", fontsize=9)

ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
ax.set_title("P=[[1,0],[0,0]]: rank 1 (x-axis) + nullity 1 (y-axis) = 2")
ax.legend(loc="lower right", fontsize=8)
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)             # build_figures.py reads this
