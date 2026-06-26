"""The Mandelbrot set: which c keep z_{n+1}=z_n^2+c bounded."""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

W, H = 900, 700
re = np.linspace(-2.2, 0.8, W)
im = np.linspace(-1.2, 1.2, H)
C = re[np.newaxis, :] + 1j * im[:, np.newaxis]
Z = np.zeros_like(C)
escape = np.zeros(C.shape, dtype=float)
maxit = 200
alive = np.ones(C.shape, dtype=bool)
for n in range(maxit):
    Z[alive] = Z[alive] * Z[alive] + C[alive]
    diverged = alive & (np.abs(Z) > 2.0)
    escape[diverged] = n
    alive &= ~diverged
escape[alive] = maxit

fig, ax = plt.subplots(figsize=(7.2, 5.8))
ax.imshow(np.log1p(escape), extent=(-2.2, 0.8, -1.2, 1.2),
          cmap="magma", origin="lower")
ax.set_xlabel("Re(c)")
ax.set_ylabel("Im(c)")
ax.set_title("Mandelbrot set (black = bounded; boundary is a fractal)")
fig.tight_layout()
fig.savefig(OUT / "ch12-mandelbrot.svg")
print("wrote ch12-mandelbrot.svg")
