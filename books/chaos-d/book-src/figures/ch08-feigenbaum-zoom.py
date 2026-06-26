"""Bifurcation self-similarity: full view + zoom showing the same fork shape."""
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out"; OUT.mkdir(exist_ok=True)
BG, INK, ACC = "#fdfcf9", "#16324f", "#c0532b"

def diagram(rmin, rmax, nx=1600, trans=600, samp=260, xlim=None):
    rs = np.linspace(rmin, rmax, nx); R, X = [], []
    for r in rs:
        x = 0.5
        for _ in range(trans): x = r * x * (1 - x)
        for _ in range(samp):
            x = r * x * (1 - x)
            if xlim is None or (xlim[0] <= x <= xlim[1]):
                R.append(r); X.append(x)
    return R, X

fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 3.8))
for ax in (a1, a2):
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG); ax.tick_params(colors=INK)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(INK)

R, X = diagram(3.4, 4.0)
a1.scatter(R, X, s=0.06, color=INK, alpha=0.35, rasterized=True, linewidths=0)
a1.add_patch(plt.Rectangle((3.847, 0.46), 0.013, 0.10, fill=False, ec=ACC, lw=1.2))
a1.set_title("full view", color=INK, fontsize=10)
a1.set_xlabel("r", color=INK); a1.set_ylabel("xₙ", color=INK); a1.set_ylim(0, 1)

# zoom into a period-3 window's own doubling cascade (same fork shape)
R2, X2 = diagram(3.847, 3.860, nx=1400, xlim=(0.46, 0.56))
a2.scatter(R2, X2, s=0.10, color=INK, alpha=0.45, rasterized=True, linewidths=0)
a2.set_title("zoom: a smaller copy of the same forking", color=INK, fontsize=10)
a2.set_xlabel("r (zoom)", color=INK); a2.set_ylim(0.46, 0.56)
fig.suptitle("Self-similarity: each fork is a shrunk copy → one constant δ ≈ 4.669",
             color=INK, fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(OUT / "ch08-feigenbaum-zoom.svg", facecolor=BG, bbox_inches="tight", dpi=150)
print("ok ch08-feigenbaum-zoom")
