"""Mandelbrot set: escape-time of z -> z^2 + c. imshow (raster embedded in SVG)."""
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out"; OUT.mkdir(exist_ok=True)
BG = "#fdfcf9"
W, H, ITER = 900, 700, 200
re = np.linspace(-2.2, 0.8, W); im = np.linspace(-1.25, 1.25, H)
C = re[None, :] + 1j * im[:, None]
Z = np.zeros_like(C); div = np.full(C.shape, ITER, dtype=float)
alive = np.ones(C.shape, bool)
for k in range(ITER):
    Z[alive] = Z[alive] ** 2 + C[alive]
    esc = alive & (np.abs(Z) > 2)
    div[esc] = k; alive &= ~esc
div[alive] = 0  # inside the set -> 0 (rendered dark)

fig, ax = plt.subplots(figsize=(6.4, 5.2))
fig.patch.set_facecolor(BG)
ax.imshow(np.log1p(div), cmap="bone_r", extent=[-2.2, 0.8, -1.25, 1.25], origin="lower")
ax.set_xlabel("Re(c)"); ax.set_ylabel("Im(c)")
ax.set_title("Mandelbrot set: which c keep z→z²+c bounded", fontsize=10.5)
fig.tight_layout()
fig.savefig(OUT / "ch12-mandelbrot.svg", facecolor=BG, bbox_inches="tight", dpi=150)
print("ok ch12-mandelbrot")
