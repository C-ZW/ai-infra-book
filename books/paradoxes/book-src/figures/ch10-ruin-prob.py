# ch10 figure: ruin probability as a function of starting capital i, pot N=100.
# Fair game (p=q=0.5) gives the straight line 1 - i/N.
# Biased game (American roulette, p=18/38 win, q=20/38 lose) gives a convex
# curve that stays near 1 almost everywhere -- the house-edge effect.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch10-ruin-prob.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

N = 100
p, q = 18 / 38, 20 / 38
r = q / p  # > 1 because the house has the edge

xs = list(range(0, N + 1))
fair = [1 - i / N for i in xs]


def biased_ruin(i, N, r):
    if i == 0:
        return 1.0
    if i == N:
        return 0.0
    return (r**i - r**N) / (1 - r**N)


biased = [biased_ruin(i, N, r) for i in xs]

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(xs, fair, color="#2b6cb0", lw=2.2, label="fair game, p = q = 1/2 (straight line)")
ax.plot(xs, biased, color="#c0392b", lw=2.2,
         label="American roulette, p = 18/38 (curves back to 1)")
ax.set_xlabel("starting capital i (pot N = 100)")
ax.set_ylabel("ruin probability")
ax.set_ylim(-0.03, 1.05)
ax.legend(loc="center left", fontsize=9)
ax.set_title("Ruin probability vs starting capital: fair vs house-edge game")
fig.tight_layout()
fig.savefig(OUT)
print("wrote", OUT)
