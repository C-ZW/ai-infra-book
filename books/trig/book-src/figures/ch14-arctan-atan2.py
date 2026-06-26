# ch14 figure: arcsin/arctan principal branches (left) and atan2 four-quadrant coverage (right)
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch14-arctan-atan2.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 5))

# --- Left: principal-branch curves with range bands ---
x1 = np.linspace(-1, 1, 400)                 # arcsin domain [-1, 1]
xt = np.linspace(-6, 6, 600)                 # arctan domain (all reals, sampled)
axL.axhspan(-np.pi/2, np.pi/2, color="#d9ecff", alpha=0.7, label="range (-pi/2, pi/2)")
axL.plot(x1, np.arcsin(x1), color="#c0392b", lw=2, label="arcsin x  [-1,1]->[-pi/2,pi/2]")
axL.plot(xt, np.arctan(xt), color="#27ae60", lw=2, label="arctan x  R->(-pi/2,pi/2)")
axL.axhline(np.pi/2, color="#888", ls="--", lw=0.8)
axL.axhline(-np.pi/2, color="#888", ls="--", lw=0.8)
axL.set_yticks([-np.pi/2, 0, np.pi/2]); axL.set_yticklabels(["-pi/2", "0", "pi/2"])
axL.set_title("Principal branches (range is the trap)")
axL.set_xlabel("x"); axL.set_ylabel("angle (rad)"); axL.legend(loc="lower right", fontsize=8)

# --- Right: four quadrants colored by atan2 range (-pi, pi] vs atan's (-pi/2, pi/2) ---
g = np.linspace(-1, 1, 240)
X, Y = np.meshgrid(g, g)
A = np.arctan2(Y, X)                          # full angle in (-pi, pi]
im = axR.pcolormesh(X, Y, A, cmap="hsv", shading="auto", vmin=-np.pi, vmax=np.pi,
                    rasterized=True)   # rasterize only the dense mesh; keeps SVG small
axR.axvspan(0, 1, color="white", alpha=0.0)   # placeholder; right half is atan's reach
axR.axvline(0, color="k", lw=0.8); axR.axhline(0, color="k", lw=0.8)
# mark the two halves atan can/cannot express
axR.text(0.45, 0.9, "x>0: atan OK", fontsize=8, ha="center")
axR.text(-0.55, 0.9, "x<0: atan FAILS", fontsize=8, ha="center", color="white")
axR.set_aspect("equal")
axR.set_title("atan2(y,x): full (-pi, pi]  /  atan: only x>0")
axR.set_xlabel("x"); axR.set_ylabel("y")
fig.colorbar(im, ax=axR, label="atan2 angle (rad)", ticks=[-np.pi, 0, np.pi])

fig.savefig(OUT, bbox_inches="tight", dpi=150)
print("wrote", OUT)            # build_figures.py reads this
