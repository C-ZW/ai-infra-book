# ch02 figure: Monte Carlo simulation of the Monty Hall switch-vs-stay decision (~10000 trials).
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch02-simulation.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(2)
trials = 10000
car = rng.integers(1, 4, size=trials)
pick = rng.integers(1, 4, size=trials)


def host_opens(c, p):
    goats = [d for d in (1, 2, 3) if d != c and d != p]   # host always reveals a goat
    return rng.choice(goats)


host = np.array([host_opens(c, p) for c, p in zip(car, pick)])
switch_final = np.array([[d for d in (1, 2, 3) if d != p and d != h][0]
                          for p, h in zip(pick, host)])

stay_rate = float(np.mean(pick == car))
switch_rate = float(np.mean(switch_final == car))

fig, ax = plt.subplots(figsize=(5.5, 4.5))
bars = ax.bar(["stay", "switch"], [stay_rate, switch_rate],
              color=["#c0392b", "#1f8a55"], width=0.5)
ax.axhline(1 / 3, color="#c0392b", ls="--", lw=1)
ax.axhline(2 / 3, color="#1f8a55", ls="--", lw=1)
for b, v in zip(bars, [stay_rate, switch_rate]):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.3f}", ha="center", fontsize=10)
ax.set_ylim(0, 1)
ax.set_ylabel("win rate")
ax.set_title(f"Monty Hall Monte Carlo, {trials} trials")
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
