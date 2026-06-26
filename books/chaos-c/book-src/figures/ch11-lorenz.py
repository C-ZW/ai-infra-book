"""The Lorenz attractor (x-z projection), the canonical butterfly."""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0


def f(s):
    x, y, z = s
    return np.array([sigma * (y - x), x * (rho - z) - y, x * y - beta * z])


dt = 0.005
N = 20000
s = np.array([1.0, 1.0, 1.0])
pts = np.empty((N, 3))
for i in range(N):
    k1 = f(s)
    k2 = f(s + 0.5 * dt * k1)
    k3 = f(s + 0.5 * dt * k2)
    k4 = f(s + dt * k3)
    s = s + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
    pts[i] = s

fig, ax = plt.subplots(figsize=(6.4, 5.6))
ax.plot(pts[200:, 0], pts[200:, 2], lw=0.35, color="#1f4e79", alpha=0.85)
ax.set_xlabel("x")
ax.set_ylabel("z")
ax.set_title("Lorenz attractor (σ=10, ρ=28, β=8/3), x-z view")
fig.tight_layout()
fig.savefig(OUT / "ch11-lorenz.svg")
print("wrote ch11-lorenz.svg")
