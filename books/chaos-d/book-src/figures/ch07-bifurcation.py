"""Logistic bifurcation diagram, r in [2.8, 4.0]. Dense scatter -> rasterized."""
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out"; OUT.mkdir(exist_ok=True)
BG, INK = "#fdfcf9", "#16324f"
rs = np.linspace(2.8, 4.0, 2000)
pts_r, pts_x = [], []
for r in rs:
    x = 0.5
    for _ in range(400):          # transient
        x = r * x * (1 - x)
    for _ in range(220):          # attractor sample
        x = r * x * (1 - x)
        pts_r.append(r); pts_x.append(x)

fig, ax = plt.subplots(figsize=(7.4, 4.4))
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
ax.scatter(pts_r, pts_x, s=0.06, color=INK, alpha=0.35, rasterized=True, linewidths=0)
for rr, lab in [(3.0, "r=3"), (3.4495, "1+√6"), (3.56995, "r∞"), (3.8284, "1+√8")]:
    ax.axvline(rr, color="#c0532b", lw=0.7, ls="--", alpha=0.7)
    ax.text(rr, 1.02, lab, color="#c0532b", fontsize=8, ha="center")
ax.set_xlabel("r  (the only knob)", color=INK); ax.set_ylabel("long-run xₙ", color=INK)
ax.set_title("Period-doubling road into chaos  (logistic map)", color=INK, fontsize=11)
ax.set_xlim(2.8, 4.0); ax.set_ylim(0, 1.06); ax.tick_params(colors=INK)
for s in ("top", "right"): ax.spines[s].set_visible(False)
for s in ("left", "bottom"): ax.spines[s].set_color(INK)
fig.tight_layout()
fig.savefig(OUT / "ch07-bifurcation.svg", facecolor=BG, bbox_inches="tight", dpi=150)
print("ok ch07-bifurcation")
