# ch18 figure: quadratic form x^T S x = c for spine S=[[2,1],[1,2]] is an ellipse.
# Principal axes ARE the eigenvectors: long axis along (1,-1) [lambda=1, small],
# short axis along (1,1) [lambda=3, big]. Semi-axis length = sqrt(c/lambda).
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch18-quadratic-ellipse.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

S = np.array([[2.0, 1.0], [1.0, 2.0]])           # spine: eigvals 3 and 1
c = 3.0                                           # level set x^T S x = c
th = np.linspace(0, 2 * np.pi, 400)
circle = np.vstack([np.cos(th), np.sin(th)])      # unit circle in eigen-coords
# eigen-decomp: columns are unit eigenvectors (1,1)/sqrt2 [l=3], (1,-1)/sqrt2 [l=1]
Q = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
lam = np.array([3.0, 1.0])
ellipse = Q @ (np.sqrt(c / lam)[:, None] * circle)  # x = Q diag(sqrt(c/lam)) (cos,sin)

fig, ax = plt.subplots(figsize=(6, 6))
ax.plot(ellipse[0], ellipse[1], color="#2471a3", lw=2.0, label="x^T S x = 3")
t = np.linspace(-2.2, 2.2, 2)
ax.plot(t, -t, color="#c0392b", ls="--", lw=1.2)   # long axis along (1,-1)
ax.plot(t, t, color="#27ae60", ls="--", lw=1.2)    # short axis along (1,1)
for d, col, txt in [((1, -1), "#c0392b", "(1,-1)  long  lam=1"),
                    ((1, 1), "#27ae60", "(1,1)  short  lam=3")]:
    d = np.array(d, float) / np.sqrt(2) * np.sqrt(c / (1 if d[1] < 0 else 3))
    ax.annotate("", xy=d, xytext=(0, 0), arrowprops=dict(color=col, width=2.0, headwidth=9))
    ax.text(d[0] * 1.08, d[1] * 1.08, txt, color=col, fontsize=9)

ax.set_title("x^T S x = 3 is an ellipse; axes are eigenvectors of S", fontsize=10)
ax.set_xlim(-2.4, 2.4); ax.set_ylim(-2.4, 2.4); ax.set_aspect("equal")
ax.axhline(0, color="0.6", lw=0.6); ax.axvline(0, color="0.6", lw=0.6)
ax.grid(True, color="0.9", lw=0.6)
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)             # build_figures.py reads this
