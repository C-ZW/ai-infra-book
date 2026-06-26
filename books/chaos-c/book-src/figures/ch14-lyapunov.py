"""Lyapunov exponent vs r, aligned under the bifurcation diagram."""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

R = np.linspace(2.8, 4.0, 3000)

# bifurcation data
x = 0.5 * np.ones_like(R)
for _ in range(600):
    x = R * x * (1.0 - x)
rr, xx = [], []
for _ in range(250):
    x = R * x * (1.0 - x)
    rr.append(R.copy())
    xx.append(x.copy())
rr = np.concatenate(rr)
xx = np.concatenate(xx)

# Lyapunov exponent: long-term average of ln|f'(x)| = ln|r(1-2x)|
x = 0.5 * np.ones_like(R)
for _ in range(500):
    x = R * x * (1.0 - x)
lyap = np.zeros_like(R)
M = 800
for _ in range(M):
    x = R * x * (1.0 - x)
    lyap += np.log(np.abs(R * (1.0 - 2.0 * x)) + 1e-12)
lyap /= M

fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.0, 6.4), sharex=True)
a1.scatter(rr, xx, s=0.05, color="black", alpha=0.35, marker=".", linewidths=0,
           rasterized=True)
a1.set_ylabel("x (attractor)")
a1.set_title("Bifurcation diagram")
a1.set_ylim(0, 1)

a2.axhline(0, color="#c00000", lw=0.8)
a2.plot(R, lyap, color="#1f4e79", lw=0.7)
a2.set_ylabel("Lyapunov exponent λ")
a2.set_xlabel("control parameter r")
a2.set_title("λ < 0: stable     λ > 0: chaos")
a2.set_ylim(-2.0, 1.0)
a2.set_xlim(2.8, 4.0)
fig.tight_layout()
fig.savefig(OUT / "ch14-lyapunov.svg", dpi=150)
print("wrote ch14-lyapunov.svg")
