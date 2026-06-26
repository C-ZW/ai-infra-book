"""Two nearby logistic (r=4) trajectories: overlap, then exponential divergence."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out"; OUT.mkdir(exist_ok=True)
BG, INK, A, B = "#fdfcf9", "#1a1a1a", "#2b5b84", "#c0532b"

def logistic_series(x0, r, n):
    xs = [x0]
    for _ in range(n):
        x = xs[-1]; xs.append(r * x * (1 - x))
    return xs

N = 45
a = logistic_series(0.300, 4.0, N)
b = logistic_series(0.301, 4.0, N)

fig, ax = plt.subplots(figsize=(7.2, 3.4))
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
ax.plot(range(N + 1), a, color=A, lw=1.6, marker="o", ms=2.5, label="x0 = 0.300")
ax.plot(range(N + 1), b, color=B, lw=1.6, marker="o", ms=2.5, label="x0 = 0.301 (+0.001)")
ax.axvspan(0, 9, color="#000000", alpha=0.05)
ax.text(4.2, 1.06, "tracks overlap", color=INK, fontsize=9, ha="center")
ax.annotate("then diverge", xy=(20, 0.1), xytext=(27, -0.02), color=INK, fontsize=9,
            arrowprops=dict(arrowstyle="->", color=INK, lw=1))
ax.set_xlabel("step n", color=INK); ax.set_ylabel("xₙ", color=INK)
ax.set_title("Two starts differing by 0.001  (logistic, r = 4)", color=INK, fontsize=11)
ax.set_ylim(-0.08, 1.12); ax.tick_params(colors=INK)
for s in ("top", "right"): ax.spines[s].set_visible(False)
for s in ("left", "bottom"): ax.spines[s].set_color(INK)
ax.legend(frameon=False, fontsize=9, loc="lower right")
fig.tight_layout()
fig.savefig(OUT / "ch03-divergence.svg", facecolor=BG, bbox_inches="tight")
print("ok ch03-divergence")
