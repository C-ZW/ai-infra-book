# ch11 figure: eigenvectors of spine S=[[2,1],[1,2]]. The two invariant lines
# (1,1) [scaled x3, lambda=3] and (1,-1) [unmoved, lambda=1] stay on their own
# line; a generic vector (2,0) gets turned off its line. Grid shows the stretch.
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch11-eigenvectors.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

S = np.array([[2.0, 1.0], [1.0, 2.0]])          # spine: eigvals 3 and 1
fig, ax = plt.subplots(figsize=(6, 6))

t = np.linspace(-4, 4, 2)                         # the two invariant lines (dashed)
for d, col, lab in [((1, 1), "#c0392b", "eigvec (1,1), lambda=3"),
                    ((1, -1), "#2471a3", "eigvec (1,-1), lambda=1")]:
    d = np.array(d, float)
    ax.plot(t * d[0], t * d[1], color=col, lw=1.0, ls="--", alpha=0.7)

def arrow(v, col, lw=2.2):                        # draw vector v as an arrow from origin
    ax.annotate("", xy=v, xytext=(0, 0), arrowprops=dict(color=col, width=lw, headwidth=9))

for v, col in [((1, 1), "#c0392b"), ((1, -1), "#2471a3"), ((2, 0), "#7f8c8d")]:
    v = np.array(v, float); Sv = S @ v
    arrow(v, col, 1.6); arrow(Sv, col)            # v (thin) and Sv (thick), same color
    ax.text(Sv[0] + 0.1, Sv[1] + 0.1, f"S({v[0]:.0f},{v[1]:.0f})=({Sv[0]:.0f},{Sv[1]:.0f})",
            color=col, fontsize=9)

ax.set_title("S=[[2,1],[1,2]]: red & blue stay on their line; grey is turned", fontsize=10)
ax.set_xlim(-1.5, 6.5); ax.set_ylim(-2.5, 5.5); ax.set_aspect("equal")
ax.axhline(0, color="0.6", lw=0.6); ax.axvline(0, color="0.6", lw=0.6)
ax.grid(True, color="0.9", lw=0.6)
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
