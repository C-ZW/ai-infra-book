# ch02 figure: probability tree for the Monty Hall problem, fixing "you pick door 1".
# Shows how the 4 nonzero weighted atomic outcomes arise (2 impossible ones excluded).
from pathlib import Path
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch02-monty-tree.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(9.5, 6.5))


def node(x, y, text, color="0.92"):
    ax.text(x, y, text, ha="center", va="center", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.35", fc=color, ec="0.35"))


def edge(x0, y0, x1, y1, label):
    ax.plot([x0, x1], [y0, y1], color="0.45", lw=1.2, zorder=1)
    ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.16, label, fontsize=8, ha="center", color="0.15")


root = (0, 0)
node(*root, "You pick\ndoor 1")

cars = {1: (2.6, 2.4), 2: (2.6, 0.0), 3: (2.6, -2.4)}
for k, (x, y) in cars.items():
    edge(root[0], root[1], x, y, f"car = {k}  (1/3)")
    node(x, y, f"Car behind\ndoor {k}", color="#dbe9f6")

# (parent node, leaf position, edge label, leaf label, leaf color)
leaves = [
    (cars[1], (5.4, 3.2), "host opens 2\n(1/2)", "weight 1/6\nSTAY wins", "#f6dada"),
    (cars[1], (5.4, 1.6), "host opens 3\n(1/2)", "weight 1/6\nSTAY wins", "#f6dada"),
    (cars[2], (5.4, 0.0), "host FORCED\nopens 3 (prob 1)", "weight 1/3\nSWITCH wins", "#dbf6df"),
    (cars[3], (5.4, -2.4), "host FORCED\nopens 2 (prob 1)", "weight 1/3\nSWITCH wins", "#dbf6df"),
]
for (px, py), (x, y), elabel, nlabel, color in leaves:
    edge(px, py, x, y, elabel)
    node(x, y, nlabel, color=color)

ax.text(2.6, -3.7,
        "(car=2, host opens 2) and (car=3, host opens 3) never happen: weight 0",
        fontsize=8, ha="center", color="0.35")

ax.set_xlim(-1.4, 7.6)
ax.set_ylim(-4.3, 4.2)
ax.axis("off")
ax.set_title("Monty Hall: the 4 nonzero weighted atomic outcomes")
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
