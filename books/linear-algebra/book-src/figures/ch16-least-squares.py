# ch16 figure: least-squares line through three points (1,1),(2,2),(3,2).
# Fit y_hat = 2/3 + (1/2)x. Three vertical dashed residual segments show each
# point's perpendicular (in the x-axis sense) distance to the line; residuals
# -1/6, +1/3, -1/6 sum to zero. This is "solving an unsolvable equation".
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch16-least-squares.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

xs = np.array([1.0, 2.0, 3.0]); ys = np.array([1.0, 2.0, 2.0])   # the data
a, b = 2.0 / 3.0, 1.0 / 2.0                                       # intercept, slope
fit = lambda x: a + b * x

fig, ax = plt.subplots(figsize=(6, 5))
xl = np.array([0.3, 3.7])
ax.plot(xl, fit(xl), color="#2471a3", lw=2.0, label="fit  y=2/3+(1/2)x")
for x, y in zip(xs, ys):                                          # vertical residuals
    ax.plot([x, x], [y, fit(x)], color="#c0392b", ls="--", lw=1.4)
    ax.annotate(f"r={y-fit(x):+.2f}", (x, (y + fit(x)) / 2),
                color="#c0392b", fontsize=8, xytext=(6, 0),
                textcoords="offset points", va="center")
ax.scatter(xs, ys, color="#222", zorder=5, label="data points")
ax.scatter(xs, fit(xs), facecolors="none", edgecolors="#2471a3", zorder=5, label="fitted")

ax.set_title("Least squares: closest line to 3 non-collinear points", fontsize=10)
ax.set_xlabel("x"); ax.set_ylabel("y")
ax.set_xlim(0, 4); ax.set_ylim(0, 3); ax.grid(True, color="0.9", lw=0.6)
ax.legend(loc="lower right", fontsize=8)
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
