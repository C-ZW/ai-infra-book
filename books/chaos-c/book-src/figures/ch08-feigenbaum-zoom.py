"""Self-similarity of the bifurcation cascade: full view vs a zoom of one branch."""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)


def attractor(rmin, rmax, npts=2400, trans=1200, keep=400):
    R = np.linspace(rmin, rmax, npts)
    x = 0.5 * np.ones_like(R)
    for _ in range(trans):
        x = R * x * (1.0 - x)
    rr, xx = [], []
    for _ in range(keep):
        x = R * x * (1.0 - x)
        rr.append(R.copy())
        xx.append(x.copy())
    return np.concatenate(rr), np.concatenate(xx)


fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.6))

r1, x1 = attractor(2.9, 3.5699)
a1.scatter(r1, x1, s=0.07, color="black", alpha=0.35, marker=".", linewidths=0,
           rasterized=True)
a1.set_title("the period-doubling cascade")
a1.set_xlabel("r")
a1.set_ylabel("x")
a1.set_xlim(2.9, 3.5699)
a1.set_ylim(0, 1)
# box marking the zoom region (upper branch near the next split)
a1.add_patch(plt.Rectangle((3.54, 0.86), 0.029, 0.10, fill=False,
             edgecolor="#c00000", lw=1.2))

r2, x2 = attractor(3.54, 3.569)
mask = (x2 > 0.86) & (x2 < 0.96)
a2.scatter(r2[mask], x2[mask], s=0.10, color="black", alpha=0.4, marker=".",
           linewidths=0, rasterized=True)
a2.set_title("zoom of one branch: same shape again")
a2.set_xlabel("r")
a2.set_ylabel("x")
a2.set_xlim(3.54, 3.569)
a2.set_ylim(0.86, 0.96)

fig.suptitle("Feigenbaum self-similarity: spacing shrinks by ~4.669 each step",
             fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.96))
fig.savefig(OUT / "ch08-feigenbaum-zoom.svg", dpi=150)
print("wrote ch08-feigenbaum-zoom.svg")
