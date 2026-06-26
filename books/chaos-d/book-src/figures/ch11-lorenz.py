"""Lorenz attractor (sigma=10, rho=28, beta=8/3), xz projection. RK4, no scipy."""
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out"; OUT.mkdir(exist_ok=True)
BG, INK = "#fdfcf9", "#16324f"
sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0

def deriv(s):
    x, y, z = s
    return np.array([sigma * (y - x), x * (rho - z) - y, x * y - beta * z])

dt, n = 0.005, 12000
s = np.array([1.0, 1.0, 1.0]); xs, zs = [], []
for _ in range(n):
    k1 = deriv(s); k2 = deriv(s + dt / 2 * k1)
    k3 = deriv(s + dt / 2 * k2); k4 = deriv(s + dt * k3)
    s = s + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    xs.append(s[0]); zs.append(s[2])

fig, ax = plt.subplots(figsize=(5.8, 5.2))
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
ax.plot(xs, zs, color=INK, lw=0.35, alpha=0.8, rasterized=True)
ax.set_xlabel("x", color=INK); ax.set_ylabel("z", color=INK)
ax.set_title("Lorenz attractor — bounded, never repeating, never crossing", color=INK, fontsize=10.5)
ax.tick_params(colors=INK)
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
for sp in ("left", "bottom"): ax.spines[sp].set_color(INK)
fig.tight_layout()
fig.savefig(OUT / "ch11-lorenz.svg", facecolor=BG, bbox_inches="tight", dpi=150)
print("ok ch11-lorenz")
