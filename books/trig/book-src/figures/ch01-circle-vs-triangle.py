# ch01 figure: unit circle point P=(cos,sin) with axis-projection "shadows"
# overlaid on a right triangle whose hypotenuse = the radius = 1.
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch01-circle-vs-triangle.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

theta = np.deg2rad(50.0)       # the angle; change this to move P around the circle
cx, cy = np.cos(theta), np.sin(theta)

fig, ax = plt.subplots(figsize=(5, 5))
t = np.linspace(0, 2 * np.pi, 400)
ax.plot(np.cos(t), np.sin(t), color="0.6", lw=1)          # the unit circle
ax.axhline(0, color="0.8", lw=0.8); ax.axvline(0, color="0.8", lw=0.8)

# right triangle: origin -> (cos,0) -> P -> origin; hypotenuse = radius = 1
ax.plot([0, cx, cx, 0], [0, 0, cy, 0], color="C0", lw=2)
ax.plot([0, cx], [0, cy], color="C3", lw=2)               # hypotenuse = 1
ax.plot(cx, cy, "o", color="C3")                          # the point P

# the "shadows": dashed projections onto both axes
ax.plot([cx, cx], [0, cy], "--", color="C1", lw=1.2)      # shadow onto x-axis
ax.plot([0, cx], [cy, cy], "--", color="C2", lw=1.2)      # shadow onto y-axis

ax.annotate("P = (cos$\\theta$, sin$\\theta$)", (cx, cy),
            textcoords="offset points", xytext=(8, 8))
ax.text(cx / 2, -0.08, "cos$\\theta$", ha="center", color="C1")
ax.text(cx + 0.03, cy / 2, "sin$\\theta$", va="center", color="C2")
ax.text(cx / 2 - 0.05, cy / 2 + 0.04, "r = 1", color="C3", rotation=np.rad2deg(theta))
ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.2, 1.2)
ax.set_aspect("equal")         # for circle/rotation figures, keep it round
ax.set_title("A point on the unit circle and its shadows")
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
