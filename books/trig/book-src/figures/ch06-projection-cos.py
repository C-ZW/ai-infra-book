# ch06 figure: projection of b onto a (foot + dashed drop), angle theta, projection length |b|cos(theta)
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch06-projection-cos.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

a = np.array([3.0, 4.0]); b = np.array([4.0, 3.0])     # worked-example vectors
proj_scalar = a.dot(b) / np.linalg.norm(a)             # |b|cos(theta) = 24/5 = 4.8
foot = (a.dot(b) / a.dot(a)) * a                       # foot of perpendicular on line a -> (2.88, 3.84)
theta = np.degrees(np.arccos(a.dot(b)/(np.linalg.norm(a)*np.linalg.norm(b))))

fig, ax = plt.subplots(figsize=(5, 5))
ax.quiver(0, 0, *a, angles="xy", scale_units="xy", scale=1, color="C0", label="a = (3,4)")
ax.quiver(0, 0, *b, angles="xy", scale_units="xy", scale=1, color="C3", label="b = (4,3)")
ax.plot([b[0], foot[0]], [b[1], foot[1]], "k--", lw=1)         # drop b onto line a
ax.plot([0, foot[0]], [0, foot[1]], color="C0", lw=4, alpha=0.35)  # the shadow on a
ax.plot(*foot, "ko", ms=4)                                     # foot point
ax.annotate(f"|b|cos(theta) = {proj_scalar:.1f}", (foot[0]/2, foot[1]/2-0.4), color="C0")
ax.annotate(f"theta = {theta:.2f} deg", (0.5, 0.25))
ax.axhline(0, color="0.85"); ax.axvline(0, color="0.85")
ax.set_aspect("equal"); ax.set_xlim(-0.5, 4.5); ax.set_ylim(-0.5, 4.5)
ax.legend(loc="upper left", fontsize=8)
ax.set_title("Projection = shadow: |b|cos(theta) of b onto a")
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
