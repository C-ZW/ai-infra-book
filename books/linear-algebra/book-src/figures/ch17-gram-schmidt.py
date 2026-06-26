# ch17 figure: Gram-Schmidt on the spine S=[[2,1],[1,2]] columns a1=(2,1), a2=(1,2).
# e1 = a1/|a1|; subtract a2's projection onto e1 (the (8/5,4/5) component) to get the
# orthogonal residual, then normalize to e2. Shows the two slanted inputs, the shaved-off
# projection, and the resulting orthonormal e1, e2 (e1.e2=0).
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch17-gram-schmidt.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

a1 = np.array([2.0, 1.0]); a2 = np.array([1.0, 2.0])      # the two columns of S
e1 = a1 / np.linalg.norm(a1)                              # first orthonormal vector
proj = (a2 @ a1) / (a1 @ a1) * a1                         # projection of a2 onto a1 = (8/5,4/5)
resid = a2 - proj                                         # orthogonal residual = (-3/5,6/5)
e2 = resid / np.linalg.norm(resid)                        # second orthonormal vector

def arrow(v, col, lw=2.2, ls="-"):
    ax.annotate("", xy=v, xytext=(0, 0),
                arrowprops=dict(color=col, width=lw, headwidth=9, linestyle=ls))

fig, ax = plt.subplots(figsize=(6, 6))
arrow(a1, "#7f8c8d", 1.6); ax.text(2.05, 0.9, "a1=(2,1)", color="#7f8c8d", fontsize=9)
arrow(a2, "#7f8c8d", 1.6); ax.text(0.55, 2.0, "a2=(1,2)", color="#7f8c8d", fontsize=9)
arrow(proj, "#d68910", 1.4); ax.text(1.6, 0.45, "proj=(8/5,4/5)", color="#d68910", fontsize=8)
ax.plot([proj[0], a2[0]], [proj[1], a2[1]], color="#d68910", lw=1.0, ls=":")  # a2 - proj
arrow(e1, "#c0392b"); ax.text(0.92, 0.30, "e1", color="#c0392b", fontsize=11)
arrow(e2, "#2471a3"); ax.text(-0.62, 0.85, "e2", color="#2471a3", fontsize=11)
ax.plot([0, resid[0]], [0, resid[1]], color="#2471a3", lw=1.0, ls="--", alpha=0.6)  # residual dir

ax.set_title("Gram-Schmidt on S columns: e1.e2 = %.0f  (orthonormal)" % (e1 @ e2), fontsize=10)
ax.set_xlim(-1.2, 2.6); ax.set_ylim(-0.6, 2.4); ax.set_aspect("equal")
ax.axhline(0, color="0.6", lw=0.6); ax.axvline(0, color="0.6", lw=0.6)
ax.grid(True, color="0.9", lw=0.6)
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
