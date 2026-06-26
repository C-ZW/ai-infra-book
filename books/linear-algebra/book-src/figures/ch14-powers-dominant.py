# ch14 figure: repeatedly applying spine S=[[2,1],[1,2]] to a start vector.
# Plot the orbit v, Sv, S^2 v, S^3 v, S^4 v. As n grows the points hug the
# dominant eigenvector direction (1,1) [lambda=3]; the (1,-1) [lambda=1] part
# stays fixed-size and is washed out by the 3^n growth.
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch14-powers-dominant.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

S = np.array([[2.0, 1.0], [1.0, 2.0]])          # spine: eigvals 3 (dir (1,1)) and 1 (dir (1,-1))
v0 = np.array([2.0, 0.0])                         # generic start, NOT an eigenvector
orbit = [np.linalg.matrix_power(S, k) @ v0 for k in range(5)]   # v0 .. S^4 v0

fig, ax = plt.subplots(figsize=(6, 6))
t = np.linspace(0, 1, 2)
ax.plot(t * 90, t * 90, color="#c0392b", lw=1.0, ls="--", alpha=0.8,
        label="dominant eigvec dir (1,1), lambda=3")   # the line everything aligns to

for k, p in enumerate(orbit):                    # draw each S^k v0 as an arrow + label
    ax.annotate("", xy=p, xytext=(0, 0),
                arrowprops=dict(color="#2471a3", width=1.3, headwidth=7, alpha=0.85))
    ang = np.degrees(np.arctan2(p[1], p[0]))
    ax.text(p[0] + 1.2, p[1] - 1.5, f"S^{k}v=({p[0]:.0f},{p[1]:.0f}) {ang:.0f}deg", fontsize=8)

ax.set_title("Repeated S on (2,0): orbit angle -> 45deg (the (1,1) axis)", fontsize=10)
ax.set_xlim(-5, 92); ax.set_ylim(-5, 92); ax.set_aspect("equal")
ax.axhline(0, color="0.6", lw=0.6); ax.axvline(0, color="0.6", lw=0.6)
ax.grid(True, color="0.9", lw=0.6); ax.legend(loc="upper left", fontsize=8)
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
