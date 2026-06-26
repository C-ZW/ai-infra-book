"""Cobweb plot of the logistic map at r=2.5 converging to the fixed point."""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

r = 2.5
x = np.linspace(0.0, 1.0, 500)

fig, ax = plt.subplots(figsize=(5.6, 5.6))
ax.plot(x, r * x * (1.0 - x), color="#1f4e79", lw=1.6, label="y = r x (1 - x)")
ax.plot(x, x, color="#888888", lw=1.0, label="y = x")

xi = 0.1
cx, cy = [xi], [0.0]
for _ in range(40):
    fx = r * xi * (1.0 - xi)
    cx += [xi, fx]
    cy += [fx, fx]
    xi = fx
ax.plot(cx, cy, color="#c00000", lw=0.8, alpha=0.9)

xstar = 1.0 - 1.0 / r
ax.plot([xstar], [xstar], "ko", ms=5)
ax.annotate("x* = 0.6", (xstar, xstar), textcoords="offset points",
            xytext=(10, -14), fontsize=10)
ax.set_xlabel("x_n")
ax.set_ylabel("x_n+1")
ax.set_title("Cobweb, logistic map r = 2.5 (converges)")
ax.legend(loc="upper left", fontsize=9)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_aspect("equal")
fig.tight_layout()
fig.savefig(OUT / "ch05-cobweb.svg")
print("wrote ch05-cobweb.svg")
