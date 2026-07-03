# ch10 figure: several fair (p=0.5) random-walk paths of a gambler's capital,
# starting at i=10 out of a total pot N=20, until absorption at 0 or N.
from pathlib import Path
import random
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch10-ruin-paths.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

N = 20          # total pot (absorbing barrier at top)
START = 10      # starting capital i
N_PATHS = 6
MAX_STEPS = 400

fig, ax = plt.subplots(figsize=(8.5, 5.2))
rng = random.Random(7)          # fixed seed for reproducibility
colors = plt.cm.tab10.colors

ruined, won = 0, 0
for k in range(N_PATHS):
    capital = START
    path = [capital]
    for _ in range(MAX_STEPS):
        if capital == 0 or capital == N:
            break
        capital += 1 if rng.random() < 0.5 else -1
        path.append(capital)
    if path[-1] == 0:
        ruined += 1
    elif path[-1] == N:
        won += 1
    ax.plot(range(len(path)), path, color=colors[k % 10], lw=1.4, alpha=0.85)
    ax.scatter([len(path) - 1], [path[-1]], color=colors[k % 10], s=28, zorder=3)

ax.axhline(0, color="0.2", lw=2)
ax.axhline(N, color="0.2", lw=2)
ax.text(MAX_STEPS * 0.02, 0.6, "ruin (capital = 0)", fontsize=8, color="0.2")
ax.text(MAX_STEPS * 0.02, N - 1.3, f"target (capital = {N})", fontsize=8, color="0.2")
ax.axhline(START, color="0.6", lw=0.8, ls="--")

ax.set_xlim(0, MAX_STEPS * 0.55)
ax.set_ylim(-1, N + 1)
ax.set_xlabel("number of fair bets played (step)")
ax.set_ylabel("gambler's capital")
ax.set_title(f"{N_PATHS} independent fair walks from capital = {START}, pot = {N}")
fig.tight_layout()
fig.savefig(OUT)
print("wrote", OUT, f"(ruined={ruined}, won={won} of {N_PATHS})")
