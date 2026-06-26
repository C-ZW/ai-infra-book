# ch02 figure: 1 radian = arc length equals radius; sin x vs x near origin
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch02-radian-and-smallangle.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

fig, (axL, axR) = plt.subplots(1, 2, figsize=(10, 5))

# --- Left: 1 radian = the angle whose arc length equals the radius ---
t = np.linspace(0, 2 * np.pi, 400)
axL.plot(np.cos(t), np.sin(t), color="0.7")          # full unit circle
arc = np.linspace(0, 1.0, 100)                       # arc from 0 to 1 rad
axL.plot(np.cos(arc), np.sin(arc), color="C3", lw=3) # the arc, length = r = 1
axL.plot([0, 1], [0, 0], color="C0")                 # radius along x-axis
axL.plot([0, np.cos(1)], [0, np.sin(1)], color="C0") # radius at 1 rad
axL.annotate("arc s = r", xy=(np.cos(0.5), np.sin(0.5)),
             xytext=(1.05, 0.75), color="C3")
axL.text(0.45, -0.12, "r")
axL.text(0.18, 0.05, "1 rad")
axL.set_title("1 radian:  s = r * theta,  here s = r")
axL.set_aspect("equal")        # keep the circle round
axL.set_xlim(-1.3, 1.6); axL.set_ylim(-1.3, 1.3)

# --- Right: y = sin x and y = x coincide near 0, then diverge ---
x = np.linspace(-1.5, 1.5, 400)
axR.plot(x, x, "--", color="C0", label="y = x")
axR.plot(x, np.sin(x), color="C3", label="y = sin x")
axR.axhline(0, color="0.8"); axR.axvline(0, color="0.8")
axR.set_title("near 0:  sin x ~ x  (radians)")
axR.set_xlabel("x (rad)"); axR.legend(loc="upper left")

fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
