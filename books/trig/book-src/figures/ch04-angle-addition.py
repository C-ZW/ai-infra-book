# ch04 figure: classic unit-circle construction for sin(a+b)/cos(a+b)
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch04-angle-addition.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

a, b = np.deg2rad(30), np.deg2rad(40)        # two stacked angles
O = np.array([0.0, 0.0])
P = np.array([np.cos(a + b), np.sin(a + b)]) # point at angle a+b on unit circle
D = np.cos(b) * np.array([np.cos(a), np.sin(a)])  # foot on ray of angle a: OD = cos b
Q = np.array([P[0], 0.0])                    # foot of P on x-axis: PQ = sin(a+b)

fig, ax = plt.subplots(figsize=(5, 5))
t = np.linspace(0, np.pi / 2, 100)
ax.plot(np.cos(t), np.sin(t), color="0.7", lw=1)            # unit circle arc
for X, c in [(P, "k"), (D, "k")]:                            # rays from O
    ax.plot([0, X[0]], [0, X[1]], color=c, lw=1.2)
ax.plot([D[0], P[0]], [D[1], P[1]], color="C3", lw=2)        # DP = sin b
ax.plot([P[0], Q[0]], [P[1], Q[1]], "--", color="0.5", lw=1) # P down to x-axis
ax.plot([D[0], D[0]], [0, D[1]], ":", color="C0", lw=1.5)    # cos b * sin a (lower stack)
ax.plot([Q[0], D[0]], [P[1], P[1]], ":", color="C0", lw=1)   # guide at height sin(a+b)
ax.annotate("P", P, textcoords="offset points", xytext=(4, 4))
ax.annotate("O", O, textcoords="offset points", xytext=(-12, -2))
ax.text(0.18, 0.06, "a", color="k"); ax.text(0.42, 0.30, "b", color="k")
ax.text(P[0] - 0.02, P[1] / 2, "sin(a+b)", rotation=90, va="center", ha="right", fontsize=8)
ax.text(D[0] / 2 - 0.02, D[1] / 2, "cos b·sin a", color="C0", rotation=90, va="center", ha="right", fontsize=7)
ax.text((D[0] + P[0]) / 2, (D[1] + P[1]) / 2 + 0.03, "sin b·cos a", color="C3", fontsize=7)
ax.set_xlim(-0.05, 1.05); ax.set_ylim(-0.05, 1.05)
ax.set_aspect("equal")         # keep the circle round
ax.set_xlabel("x"); ax.set_ylabel("y")
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
