# ch15 figure: dot product as projection. u=(2,1), v=(1,2), angle ~36.87 deg.
# Drop v onto u's direction: foot = (u.v/||u||^2) u = (4/5)(2,1) = (1.6,0.8).
# The dot product u.v=4 equals ||u|| times the scalar projection ||v||cos(theta).
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch15-dot-product-angle.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

u = np.array([2.0, 1.0]); v = np.array([1.0, 2.0])     # spine S's two columns
foot = (u @ v) / (u @ u) * u                            # projection of v onto u = (1.6,0.8)
theta = np.degrees(np.arccos((u @ v) / (np.linalg.norm(u) * np.linalg.norm(v))))

fig, ax = plt.subplots(figsize=(5, 5))
ax.annotate("", xy=u, xytext=(0, 0), arrowprops=dict(color="#c0392b", width=2, headwidth=10))
ax.annotate("", xy=v, xytext=(0, 0), arrowprops=dict(color="#2471a3", width=2, headwidth=10))
ax.plot([v[0], foot[0]], [v[1], foot[1]], color="#7f8c8d", ls="--", lw=1.2)   # perpendicular
ax.plot([0, foot[0]], [0, foot[1]], color="#27ae60", lw=3, alpha=0.7)         # projection length
ax.plot(*foot, "o", color="#27ae60", ms=5)
ax.text(2.05, 1.0, "u=(2,1)", color="#c0392b", fontsize=10)
ax.text(0.7, 2.05, "v=(1,2)", color="#2471a3", fontsize=10)
ax.text(0.75, 0.15, "proj = u.v/||u|| = 4/sqrt5", color="#27ae60", fontsize=9)
ax.text(1.25, 1.35, f"theta~{theta:.2f} deg", color="0.2", fontsize=9)
ax.set_title("Dot product = projection:  u.v = ||u|| * (||v|| cos theta) = 4", fontsize=10)
ax.set_xlim(-0.4, 2.8); ax.set_ylim(-0.4, 2.8); ax.set_aspect("equal")
ax.axhline(0, color="0.6", lw=0.6); ax.axvline(0, color="0.6", lw=0.6)
ax.grid(True, color="0.9", lw=0.6)
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
