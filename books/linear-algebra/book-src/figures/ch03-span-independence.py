# ch03 figure: independent vectors span the plane vs collinear vectors span a line
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch03-span-independence.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

fig, (axL, axR) = plt.subplots(1, 2, figsize=(10, 5))
rng = range(-4, 5)                              # integer combination coeffs a, b

# LEFT: v1=(2,1), v2=(1,2) are independent -> combinations fill the plane (lattice)
v1, v2 = np.array([2, 1]), np.array([1, 2])
pts = np.array([a * v1 + b * v2 for a in rng for b in rng])
axL.scatter(pts[:, 0], pts[:, 1], s=10, color="0.7", label="a·v1 + b·v2")
for v, col, name in [(v1, "tab:red", "v1=(2,1)"), (v2, "tab:blue", "v2=(1,2)")]:
    axL.annotate("", xy=v, xytext=(0, 0), arrowprops=dict(arrowstyle="->", color=col, lw=2.5))
    axL.annotate(name, xy=v, color=col, fontsize=10)
axL.set_title("Independent: span = whole plane")

# RIGHT: w1=(1,2), w2=(2,4)=2*w1 are collinear -> every combination lands on y=2x
w1, w2 = np.array([1, 2]), np.array([2, 4])
line = np.array([a * w1 + b * w2 for a in rng for b in rng])     # all on the line
axR.plot([-6, 6], [-12, 12], color="0.85", lw=1)                 # the line y = 2x
axR.scatter(line[:, 0], line[:, 1], s=10, color="0.7", label="c·w1 + d·w2")
for v, col, name in [(w1, "tab:red", "w1=(1,2)"), (w2, "tab:blue", "w2=(2,4)=2·w1")]:
    axR.annotate("", xy=v, xytext=(0, 0), arrowprops=dict(arrowstyle="->", color=col, lw=2.5))
    axR.annotate(name, xy=v, color=col, fontsize=9)
axR.set_title("Dependent: span = one line (y = 2x)")

for ax in (axL, axR):
    ax.axhline(0, color="0.9", lw=0.8); ax.axvline(0, color="0.9", lw=0.8)
    ax.set_xlim(-6, 6); ax.set_ylim(-6, 6)
    ax.set_aspect("equal"); ax.legend(loc="upper left", fontsize=8)

fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)             # build_figures.py reads this
