"""Bifurcation diagram of the logistic map, r in [2.8, 4.0]."""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

R = np.linspace(2.8, 4.0, 3000)
x = 0.5 * np.ones_like(R)
for _ in range(600):           # transient
    x = R * x * (1.0 - x)

rr, xx = [], []
for _ in range(300):           # collect attractor
    x = R * x * (1.0 - x)
    rr.append(R.copy())
    xx.append(x.copy())
rr = np.concatenate(rr)
xx = np.concatenate(xx)

fig, ax = plt.subplots(figsize=(9.0, 5.2))
ax.scatter(rr, xx, s=0.06, color="black", alpha=0.35, marker=".", linewidths=0,
           rasterized=True)
for rc, lbl in [(3.0, "r=3"), (3.4495, "1+√6"), (3.5699, "r∞"), (3.8284, "1+√8")]:
    ax.axvline(rc, color="#c00000", lw=0.6, ls="--", alpha=0.6)
    ax.text(rc, 1.02, lbl, color="#c00000", fontsize=8, ha="center")
ax.set_xlabel("control parameter r")
ax.set_ylabel("long-term values of x")
ax.set_title("Logistic map bifurcation diagram")
ax.set_xlim(2.8, 4.0)
ax.set_ylim(0, 1.06)
fig.tight_layout()
fig.savefig(OUT / "ch07-bifurcation.svg", dpi=150)
print("wrote ch07-bifurcation.svg")
