# ch21 figure: four-node Braess network, before vs. after adding the B->C shortcut.
#
# Base numbers (must match the worked example in the chapter text):
#   Before: symmetric equilibrium at x=0.5, equilibrium travel time = 1.50.
#   After (shortcut cost 0): all flow funnels through B->C, travel time = 2.00.
# English-only in-image labels: this machine's matplotlib has no bundled CJK
# glyphs, so Chinese text renders as tofu boxes. The Traditional Chinese
# caption lives in the chapter markdown's ![...] alt text instead.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch21-braess-network.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

NODES = {"S": (0, 0.5), "B": (1, 1.0), "C": (1, 0.0), "E": (2, 0.5)}


def draw_node(ax, name):
    x, y = NODES[name]
    ax.add_patch(plt.Circle((x, y), 0.11, facecolor="#eef3fb", edgecolor="#1f5fa8", lw=1.6, zorder=3))
    ax.text(x, y, name, ha="center", va="center", fontsize=13, fontweight="bold", zorder=4)


def draw_edge(ax, a, b, label, color="#333333", style="-"):
    xa, ya = NODES[a]
    xb, yb = NODES[b]
    ax.annotate("", xy=(xb, yb), xytext=(xa, ya),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.7, linestyle=style,
                                 shrinkA=14, shrinkB=14))
    lx = (xa + xb) / 2 + (0.16 if xa == xb else 0)
    ly = (ya + yb) / 2
    ax.text(lx, ly, label, fontsize=9.5, color=color, ha="center",
            va="bottom" if yb >= ya else "top")


def panel(ax, with_shortcut, ue_value, title):
    for n in NODES:
        draw_node(ax, n)
    draw_edge(ax, "S", "B", "cost = x")
    draw_edge(ax, "S", "C", "cost = 1")
    draw_edge(ax, "B", "E", "cost = 1")
    draw_edge(ax, "C", "E", "cost = x")
    if with_shortcut:
        draw_edge(ax, "B", "C", "cost = 0 (new)", color="#c0392b", style="--")
    ax.set_xlim(-0.4, 2.4)
    ax.set_ylim(-0.4, 1.4)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"{title}\nequilibrium travel time = {ue_value:.2f}", fontsize=11)


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5.2))
panel(ax1, False, 1.50, "Before: two symmetric routes")
panel(ax2, True, 2.00, "After: B->C shortcut added")
fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
