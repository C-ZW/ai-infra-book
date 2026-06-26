# ch19 figure: SVD sends the unit circle to an ellipse, in three steps.
# Top: unit circle + grid sent by spine S=[[2,1],[1,2]] to an ellipse (semi-axes 3,1).
# Bottom: the same map factored as V^T (rotate) -> Sigma (stretch on axes) -> U (rotate).
# Spine S is symmetric positive definite, so U=V=Q and the singular values 3,1 ARE its eigenvalues.
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch19-svd-circle-ellipse.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

S = np.array([[2.0, 1.0], [1.0, 2.0]])           # spine: singular values 3 and 1
U, sig, Vt = np.linalg.svd(S)                     # S = U diag(sig) Vt
th = np.linspace(0, 2 * np.pi, 400)
circ = np.vstack([np.cos(th), np.sin(th)])        # unit circle
e1 = np.array([1.0, 0.0]); e2 = np.array([0.0, 1.0])

def draw(ax, M, title, base):                     # plot M @ (circle, e1, e2) over a base grid
    P = M @ circ
    ax.plot(circ[0], circ[1], color="0.8", lw=1.0)            # faint unit circle
    ax.plot(P[0], P[1], color="#2471a3", lw=2.0)              # image curve
    for v, col in [(e1, "#c0392b"), (e2, "#27ae60")]:
        w = M @ v
        ax.annotate("", xy=w, xytext=(0, 0), arrowprops=dict(color=col, width=1.6, headwidth=8))
    ax.set_title(title, fontsize=9)
    ax.set_xlim(-3.4, 3.4); ax.set_ylim(-3.4, 3.4); ax.set_aspect("equal")
    ax.axhline(0, color="0.7", lw=0.5); ax.axvline(0, color="0.7", lw=0.5)
    ax.grid(True, color="0.92", lw=0.5)

fig, ax = plt.subplots(2, 2, figsize=(8, 8))
draw(ax[0, 0], np.eye(2), "unit circle (before)", None)
draw(ax[0, 1], S, "S sends circle -> ellipse (semi-axes 3,1)", None)
draw(ax[1, 0], np.diag(sig) @ Vt, "step1+2: V^T rotate, then Sigma stretch", None)
draw(ax[1, 1], U @ np.diag(sig) @ Vt, "step3: U rotate -> same ellipse", None)
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)             # build_figures.py reads this
