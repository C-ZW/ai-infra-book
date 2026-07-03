# ch14 figure: three capital trajectories over the same number of turns.
# Game A alone (biased coin, loses), Game B alone (capital mod 3 decides which
# coin to use, loses), and a 50/50 random mix of A and B each turn (wins).
from pathlib import Path
import random
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch14-parrondo-capital.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

EPS = 0.005
P1 = 0.5 - EPS          # game A win prob, capital-independent
P2 = 0.1 - EPS          # game B "bad" coin, used when capital % 3 == 0
P3 = 0.75 - EPS         # game B "good" coin, used otherwise
STEPS = 4000

rng = random.Random(42)


def play_A(capital, r):
    return capital + 1 if r.random() < P1 else capital - 1


def play_B(capital, r):
    p = P2 if capital % 3 == 0 else P3
    return capital + 1 if r.random() < p else capital - 1


def run(mode, r):
    capital = 0
    path = [0]
    for _ in range(STEPS):
        if mode == "A":
            capital = play_A(capital, r)
        elif mode == "B":
            capital = play_B(capital, r)
        else:  # 50/50 random mix each turn
            capital = play_A(capital, r) if r.random() < 0.5 else play_B(capital, r)
        path.append(capital)
    return path

path_A = run("A", rng)
path_B = run("B", rng)
path_mix = run("mix", rng)

fig, ax = plt.subplots(figsize=(8.5, 5.2))
ax.plot(path_A, color="#c0392b", lw=1.4, label="Game A alone (loses)")
ax.plot(path_B, color="#d68910", lw=1.4, label="Game B alone (loses)")
ax.plot(path_mix, color="#1e8449", lw=1.8, label="50/50 random mix of A and B (wins)")
ax.axhline(0, color="#888888", lw=0.8, ls="--")
ax.set_xlabel("turn")
ax.set_ylabel("cumulative capital")
ax.set_title("Parrondo's paradox: two losing games, one winning mixture")
ax.legend(loc="upper left", fontsize=9)
fig.tight_layout()
fig.savefig(OUT)
print("wrote", OUT)
