# ch26 figure: paradoxical decomposition of the free group F2 on its Cayley tree.
# Left panel: the tree split into the 5 original pieces {e}, W(a), W(a^-1), W(b), W(b^-1).
# Right panel: the same tree re-grouped into 2 pieces, F2 = W(a) union a.W(a^-1),
# i.e. one branch left untouched, the rest recovered by translating another branch.
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch26-free-group.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

DEPTH = 4
STEP = 1.0
SHRINK = 0.58
DIRS = (0, 90, 180, 270)


def draw(ax, x, y, depth, length, color_fn, exclude=None, first=None):
    if depth == 0:
        return
    for d in DIRS:
        if d == exclude:
            continue
        rad = np.deg2rad(d)
        nx, ny = x + length * np.cos(rad), y + length * np.sin(rad)
        f = d if first is None else first
        ax.plot([x, nx], [y, ny], color=color_fn(f), lw=max(0.6, 2.4 - depth * 0.35),
                solid_capstyle="round")
        draw(ax, nx, ny, depth - 1, length * SHRINK, color_fn, (d + 180) % 360, f)


# direction -> generator label, and a distinct color per generator
label_of = {90: "a", 270: "a$^{-1}$", 0: "b", 180: "b$^{-1}$"}
color_of = {90: "#1565c0", 270: "#c62828", 0: "#2e7d32", 180: "#f9a825"}

fig, axes = plt.subplots(1, 2, figsize=(11, 5.4))

ax = axes[0]
draw(ax, 0, 0, DEPTH, STEP, lambda f: color_of[f])
ax.plot(0, 0, "ko", ms=6, zorder=5)
for d, lab in label_of.items():
    rad = np.deg2rad(d)
    ax.text(1.35 * np.cos(rad), 1.35 * np.sin(rad), lab, ha="center", va="center", fontsize=12)
ax.set_title("original 5 pieces: e, W(a), W(a$^{-1}$), W(b), W(b$^{-1}$)", fontsize=10)
ax.set_aspect("equal")
ax.axis("off")

ax = axes[1]
two_color = lambda f: "#1565c0" if f == 90 else "#9e9e9e"  # blue = W(a); grey = the rest
draw(ax, 0, 0, DEPTH, STEP, two_color)
ax.plot(0, 0, "ko", ms=6, zorder=5)
ax.set_title("regrouped into 2 pieces: W(a)  and  a·W(a$^{-1}$) = everything else", fontsize=10)
ax.set_aspect("equal")
ax.axis("off")

fig.suptitle("Cayley tree of the free group F2: same tree, two paradoxical groupings")
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
