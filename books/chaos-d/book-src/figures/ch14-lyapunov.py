"""Lyapunov exponent lambda(r) under the bifurcation diagram. lambda>0 == chaos."""
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out"; OUT.mkdir(exist_ok=True)
BG, INK, ACC = "#fdfcf9", "#16324f", "#c0532b"
rs = np.linspace(2.8, 4.0, 1600)

# bifurcation (top)
BR, BX = [], []
for r in rs[::1]:
    x = 0.5
    for _ in range(400): x = r * x * (1 - x)
    for _ in range(160):
        x = r * x * (1 - x); BR.append(r); BX.append(x)

# lyapunov (bottom)
lam = []
for r in rs:
    x = 0.5
    for _ in range(300): x = r * x * (1 - x)
    s = 0.0; m = 600
    for _ in range(m):
        x = r * x * (1 - x)
        d = abs(r * (1 - 2 * x))
        s += np.log(d) if d > 1e-12 else -30.0
    lam.append(s / m)
lam = np.array(lam)

fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.4, 5.4), sharex=True,
                             gridspec_kw={"height_ratios": [1.3, 1]})
for ax in (a1, a2):
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG); ax.tick_params(colors=INK)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(INK)

a1.scatter(BR, BX, s=0.05, color=INK, alpha=0.3, rasterized=True, linewidths=0)
a1.set_ylabel("long-run xₙ", color=INK); a1.set_ylim(0, 1)
a1.set_title("Bifurcation (top) and its Lyapunov exponent λ(r) (bottom)", color=INK, fontsize=11)

a2.axhline(0, color=ACC, lw=1.0)
a2.plot(rs, np.clip(lam, -1.2, 1.0), color=INK, lw=0.8, rasterized=True)
a2.fill_between(rs, 0, np.clip(lam, 0, 1.0), where=lam > 0, color=ACC, alpha=0.25)
a2.text(3.9, 0.55, "λ > 0  ⇔  chaos", color=ACC, fontsize=9, ha="right")
a2.set_ylabel("λ", color=INK); a2.set_xlabel("r", color=INK)
a2.set_xlim(2.8, 4.0); a2.set_ylim(-1.2, 0.9)
fig.tight_layout()
fig.savefig(OUT / "ch14-lyapunov.svg", facecolor=BG, bbox_inches="tight", dpi=150)
print("ok ch14-lyapunov")
