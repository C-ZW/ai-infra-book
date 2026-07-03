# ch07 figure: Simpson's paradox, general mechanism.
#
# Two synthetic groups, each with a mild positive within-group trend (slope
# up as x grows), but Group 1 sits at low-x/high-y and Group 2 sits at
# high-x/low-y. Pooling both groups and fitting one regression line produces
# a trend that slopes DOWN across the full range -- the geometric picture
# behind every Simpson's-paradox reversal (incl. the Berkeley admissions
# case worked through numerically in the chapter text).
#
# All in-image text is English/numbers only: matplotlib on this machine has
# no bundled CJK glyphs, so Chinese text renders as tofu boxes. The
# Traditional Chinese caption lives in the chapter markdown's ![...] alt text.
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch07-simpson-reversal.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(7)

# Group 1: low x, high y, mild positive local slope.
x1 = np.linspace(0, 3, 18) + rng.normal(0, 0.15, 18)
y1 = 8.0 + 0.6 * x1 + rng.normal(0, 0.35, 18)

# Group 2: high x, low y, mild positive local slope.
x2 = np.linspace(5, 8, 18) + rng.normal(0, 0.15, 18)
y2 = 1.0 + 0.6 * (x2 - 5) + rng.normal(0, 0.35, 18)

fig, ax = plt.subplots(figsize=(7.2, 5.6))
ax.scatter(x1, y1, color="#1565c0", label="Group 1 (own trend: up)", s=32)
ax.scatter(x2, y2, color="#e65100", label="Group 2 (own trend: up)", s=32)

for x, y, c in ((x1, y1, "#1565c0"), (x2, y2, "#e65100")):
    a, b = np.polyfit(x, y, 1)
    xs = np.linspace(x.min(), x.max(), 2)
    ax.plot(xs, a * xs + b, color=c, linewidth=2.4)

x_all = np.concatenate([x1, x2])
y_all = np.concatenate([y1, y2])
a_all, b_all = np.polyfit(x_all, y_all, 1)
xs_all = np.linspace(x_all.min(), x_all.max(), 2)
ax.plot(xs_all, a_all * xs_all + b_all, color="black", linestyle="--",
        linewidth=2.2, label="Pooled trend (down)")

ax.set_xlabel("X (illustrative independent variable)")
ax.set_ylabel("Y (illustrative outcome)")
ax.set_title("Simpson's paradox: within-group slope up, pooled slope down")
ax.legend(loc="upper right", fontsize=9, frameon=False)
fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
