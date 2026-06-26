"""Delay-coordinate plot: logistic r=4 reveals a parabola; white noise is a cloud."""
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out"; OUT.mkdir(exist_ok=True)
BG, INK, ACC = "#fdfcf9", "#16324f", "#c0532b"
rng = np.random.default_rng(7)

x = 0.4; xs = []
for _ in range(4000):
    x = 4 * x * (1 - x); xs.append(x)
xs = np.array(xs)
u = rng.random(4000)

fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.8, 3.9))
for ax in (a1, a2):
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG); ax.tick_params(colors=INK)
    ax.set_aspect("equal")
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(INK)

a1.scatter(xs[:-1], xs[1:], s=1.2, color=INK, alpha=0.5, rasterized=True, linewidths=0)
a1.set_title("chaos (logistic r=4): a clean parabola", color=INK, fontsize=10)
a1.set_xlabel("xₙ", color=INK); a1.set_ylabel("xₙ₊₁", color=INK)

a2.scatter(u[:-1], u[1:], s=1.2, color=ACC, alpha=0.5, rasterized=True, linewidths=0)
a2.set_title("white noise: a structureless cloud", color=INK, fontsize=10)
a2.set_xlabel("uₙ", color=INK); a2.set_ylabel("uₙ₊₁", color=INK)
fig.suptitle("Same 'random-looking' series, told apart by delay coordinates",
             color=INK, fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(OUT / "ch17-embedding.svg", facecolor=BG, bbox_inches="tight", dpi=150)
print("ok ch17-embedding")
