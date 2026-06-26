# ch13 figure: epicycles (tip-to-tail rotating arrows) vs square-wave partial sums (1,3,5 terms)
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch13-epicycles-square.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 4.6))

# LEFT: odd harmonics 1,3,5 as rotating arrows chained tip-to-tail at one instant t
t = 1.0
ks = [1, 3, 5]                                   # odd harmonics only
x, y = 0.0, 0.0
for k in ks:
    r = 4 / (np.pi * k)                          # radius = coefficient 4/(k*pi)
    nx, ny = x + r * np.cos(k * t), y + r * np.sin(k * t)
    axL.plot([x, nx], [y, ny], "-o", lw=2, ms=3) # one arrow of the chain
    ang = np.linspace(0, 2 * np.pi, 100)         # its dotted orbit circle
    axL.plot(x + r * np.cos(ang), y + r * np.sin(ang), ":", color="0.7", lw=0.8)
    x, y = nx, ny
axL.plot(x, 0, "k.", ms=8)                        # tip's height = the wave value
axL.axhline(0, color="0.85"); axL.axvline(0, color="0.85")
axL.set_aspect("equal"); axL.set_title("Epicycles: arrows 4/(k*pi), k=1,3,5 tip-to-tail")

# RIGHT: square-wave partial sums with 1, 3, 5 terms (overshoot near the jump)
xs = np.linspace(-np.pi, 2 * np.pi, 2000)
square = np.where(np.mod(xs, 2 * np.pi) < np.pi, 1.0, -1.0)
axR.plot(xs, square, color="0.6", lw=1, label="square wave")
for n, c in [(1, "C0"), (3, "C2"), (5, "C3")]:
    s = sum((4 / (np.pi * k)) * np.sin(k * xs) for k in range(1, 2 * n, 2))
    axR.plot(xs, s, color=c, lw=1.6, label=f"{n} term(s)")
axR.axvline(np.pi / 2, color="0.85", ls="--")     # x = pi/2: 3-term sum = 1.10347
axR.set_title("Square-wave partial sums (Gibbs overshoot)")
axR.legend(loc="lower right", fontsize=8)
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
