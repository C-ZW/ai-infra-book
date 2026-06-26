# ch09 figure: nth roots of unity (n=3,5,8) on the unit circle joined into regular n-gons
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch09-roots-of-unity.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

fig, axes = plt.subplots(1, 3, figsize=(12, 4.2))
circ = np.linspace(0, 2 * np.pi, 200)
for ax, n, color in zip(axes, (3, 5, 8), ("C0", "C2", "C3")):
    ax.plot(np.cos(circ), np.sin(circ), color="0.8", lw=1)   # unit circle
    k = np.arange(n)
    ang = 2 * np.pi * k / n                                   # root angles 2*pi*k/n
    x, y = np.cos(ang), np.sin(ang)
    poly = np.append(np.arange(n), 0)                         # close the n-gon
    ax.plot(x[poly], y[poly], color=color, lw=1.6)            # regular n-gon edges
    ax.scatter(x, y, color=color, zorder=3)                   # the n roots
    for j in range(n):                                        # label each angle
        ax.annotate(f"2pi*{j}/{n}", (x[j], y[j]),
                    textcoords="offset points", xytext=(6, 4), fontsize=7)
    ax.axhline(0, color="0.9"); ax.axvline(0, color="0.9")
    ax.set_aspect("equal"); ax.set_xlim(-1.4, 1.4); ax.set_ylim(-1.4, 1.4)
    ax.set_title(f"n = {n}  (z^{n} = 1)")
fig.suptitle("Roots of unity: dividing the circle into n equal parts")
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
