"""Two nearby seeds in the logistic map at r=4 diverge (sensitive dependence)."""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)


def traj(x0, r, n):
    xs = [x0]
    for _ in range(n):
        xs.append(r * xs[-1] * (1.0 - xs[-1]))
    return np.array(xs)


n = 60
a = traj(0.200, 4.0, n)
b = traj(0.201, 4.0, n)
t = np.arange(n + 1)

fig, ax = plt.subplots(figsize=(8.0, 3.8))
ax.plot(t, a, "-o", ms=2.5, lw=1.0, color="#1f4e79", label="x0 = 0.200")
ax.plot(t, b, "-o", ms=2.5, lw=1.0, color="#c00000", label="x0 = 0.201")
ax.axvspan(0, 35, color="#cccccc", alpha=0.25)
ax.text(17, 1.06, "tracks overlap", ha="center", fontsize=9, color="#555")
ax.set_xlabel("step n")
ax.set_ylabel("x_n")
ax.set_title("Logistic map r = 4: two seeds differing by 0.001")
ax.legend(loc="lower right", fontsize=9)
ax.set_ylim(-0.05, 1.12)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(OUT / "ch03-divergence.svg")
print("wrote ch03-divergence.svg")
