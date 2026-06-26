# ch02 figure: linear combination 1*(2,1)+2*(1,2)=(4,5) drawn head-to-tail,
# so the geometric "face" and the coordinate "face" land on the same point.
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch02-linear-combination.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

u = np.array([2.0, 1.0])       # vector u; columns of the spine matrix S later
v = np.array([1.0, 2.0])       # vector v
# combination 1*u + 2*v: walk u once, then v twice -> path through these knots
knots = np.array([[0, 0], u, u + v, u + 2 * v])   # ends at (4,5)

fig, ax = plt.subplots(figsize=(5, 5))
ax.axhline(0, color="0.85", lw=0.8); ax.axvline(0, color="0.85", lw=0.8)
for x in range(6):             # faint integer grid so the lattice is visible
    ax.axvline(x, color="0.92", lw=0.6); ax.axhline(x, color="0.92", lw=0.6)

# the three head-to-tail steps: u (once), then v (twice)
seg = [(knots[0], u, "C0", "u=(2,1)"),
       (knots[1], v, "C1", "v=(1,2)"),
       (knots[2], v, "C1", None)]
for start, step, col, lab in seg:
    ax.annotate("", xy=start + step, xytext=start,
                arrowprops=dict(arrowstyle="->", color=col, lw=2))
    if lab:
        mid = start + step / 2
        ax.text(mid[0] + 0.08, mid[1] - 0.18, lab, color=col)

ax.plot(4, 5, "o", color="C3")                       # the result (4,5)
ax.annotate("1u + 2v = (4,5)", (4, 5),
            textcoords="offset points", xytext=(8, 4), color="C3")
ax.set_xlim(-0.5, 5.5); ax.set_ylim(-0.5, 5.5)
ax.set_aspect("equal")         # honest lengths/angles for the arrows
ax.set_title("A linear combination as head-to-tail arrows")
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
