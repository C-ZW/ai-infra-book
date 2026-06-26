# ch11 figure: velocity is position rotated +90 deg (left); sin h/h -> 1 and (1-cos h)/h -> 0 (right)
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch11-velocity-perp.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

fig, (axL, axR) = plt.subplots(1, 2, figsize=(10, 5))

# LEFT: unit circle, position (cos t, sin t) and velocity (-sin t, cos t) at three angles
t = np.linspace(0, 2 * np.pi, 200)
axL.plot(np.cos(t), np.sin(t), color="0.8", lw=1)
for a in [0.6, 2.0, 3.8]:                       # three sample angles (radians)
    px, py = np.cos(a), np.sin(a)               # position on the unit circle
    vx, vy = -np.sin(a), np.cos(a)              # velocity = position rotated +90 deg
    axL.annotate("", xy=(px, py), xytext=(0, 0),
                 arrowprops=dict(arrowstyle="->", color="C0", lw=2))           # radius
    axL.annotate("", xy=(px + 0.5 * vx, py + 0.5 * vy), xytext=(px, py),
                 arrowprops=dict(arrowstyle="->", color="C3", lw=2))           # velocity, tangent
axL.text(0.62, 0.62, "position", color="C0", fontsize=9)
axL.text(-0.95, 0.5, "velocity = pos rotated +90", color="C3", fontsize=9)
axL.set_aspect("equal")                         # keep the circle round
axL.set_xlim(-1.6, 1.6); axL.set_ylim(-1.6, 1.6)
axL.set_title("Velocity is always 90 deg ahead, tangent to circle")

# RIGHT: the two limits that the difference quotient reduces to
h = np.linspace(-1.5, 1.5, 400)
h = h[np.abs(h) > 1e-6]                          # avoid 0/0 at the origin
axR.plot(h, np.sin(h) / h, color="C0", lw=2, label="sin h / h  -> 1")
axR.plot(h, (1 - np.cos(h)) / h, color="C3", lw=2, label="(1 - cos h) / h  -> 0")
axR.axhline(1, color="0.7", ls="--", lw=0.8)
axR.axhline(0, color="0.7", ls="--", lw=0.8)
axR.set_xlabel("h (radians)"); axR.set_ylim(-0.6, 1.3)
axR.legend(loc="lower center", fontsize=9)
axR.set_title("The two limits behind sin' = cos")

fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
