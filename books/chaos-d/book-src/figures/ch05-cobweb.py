"""Cobweb plot for logistic r=2.5 converging to the fixed point x*=0.6."""
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out"; OUT.mkdir(exist_ok=True)
BG, INK, A, B = "#fdfcf9", "#1a1a1a", "#2b5b84", "#c0532b"
r = 2.5
f = lambda x: r * x * (1 - x)
xs = np.linspace(0, 1, 400)

fig, ax = plt.subplots(figsize=(5.4, 5.0))
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
ax.plot(xs, f(xs), color=A, lw=1.8, label="f(x) = 2.5·x·(1−x)")
ax.plot([0, 1], [0, 1], color=INK, lw=1.0, ls="--", label="y = x")
# cobweb
x = 0.1
for _ in range(28):
    y = f(x)
    ax.plot([x, x], [x, y], color=B, lw=0.9)
    ax.plot([x, y], [y, y], color=B, lw=0.9)
    x = y
ax.plot(0.6, 0.6, "o", color=INK, ms=6)
ax.text(0.62, 0.55, "x* = 0.6", color=INK, fontsize=10)
ax.text(0.1, 0.02, "start 0.1", color=B, fontsize=9, ha="center")
ax.set_xlabel("xₙ", color=INK); ax.set_ylabel("xₙ₊₁", color=INK)
ax.set_title("Cobweb: r = 2.5 spirals into x* = 0.6", color=INK, fontsize=11)
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal"); ax.tick_params(colors=INK)
for s in ("top", "right"): ax.spines[s].set_visible(False)
for s in ("left", "bottom"): ax.spines[s].set_color(INK)
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
fig.tight_layout()
fig.savefig(OUT / "ch05-cobweb.svg", facecolor=BG, bbox_inches="tight")
print("ok ch05-cobweb")
