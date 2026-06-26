"""Delay-coordinate scatter: deterministic chaos reveals structure, noise does not."""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

rng = np.random.default_rng(42)

# logistic r=4 series
x = 0.1
xs = []
for _ in range(2000):
    x = 4.0 * x * (1.0 - x)
    xs.append(x)
xs = np.array(xs)

# white noise on the same support
noise = rng.random(2000)

fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 4.6))

a1.scatter(xs[:-1], xs[1:], s=3, color="#1f4e79", alpha=0.6, linewidths=0)
a1.set_title("logistic r = 4: a clean parabola")
a1.set_xlabel("x_n")
a1.set_ylabel("x_n+1")
a1.set_aspect("equal")
a1.set_xlim(0, 1)
a1.set_ylim(0, 1)

a2.scatter(noise[:-1], noise[1:], s=3, color="#777777", alpha=0.5, linewidths=0)
a2.set_title("white noise: a structureless cloud")
a2.set_xlabel("x_n")
a2.set_ylabel("x_n+1")
a2.set_aspect("equal")
a2.set_xlim(0, 1)
a2.set_ylim(0, 1)

fig.suptitle("Same-looking sequences, told apart by delay coordinates", fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(OUT / "ch17-embedding.svg")
print("wrote ch17-embedding.svg")
