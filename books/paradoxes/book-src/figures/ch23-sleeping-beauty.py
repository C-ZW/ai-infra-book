# ch23 figure: Sleeping Beauty awakening tree (heads -> 1 wake, tails -> 2 wakes)
# next to two competing sample-space counts: coin-based (halfer, 1/2 each)
# vs awakening-based (thirder, 1/3 each). Same experiment, two answers.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch23-sleeping-beauty.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 5.4))


def node(ax, x, y, text, color="0.92"):
    ax.text(x, y, text, ha="center", va="center", fontsize=8.6,
            bbox=dict(boxstyle="round,pad=0.32", fc=color, ec="0.35"))


def edge(ax, x0, y0, x1, y1, label=""):
    ax.plot([x0, x1], [y0, y1], color="0.45", lw=1.2, zorder=1)
    if label:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.2, label, fontsize=7.8, ha="center")


# --- left: the awakening tree ---
node(ax1, 0, 1.6, "Sunday:\nasleep, coin flipped")
edge(ax1, 0, 1.6, 2.5, 3.1, "Heads 1/2")
edge(ax1, 0, 1.6, 2.5, 0.1, "Tails 1/2")
node(ax1, 2.5, 3.1, "Heads branch", color="#dbe9f6")
node(ax1, 2.5, 0.1, "Tails branch", color="#f6dada")

edge(ax1, 2.5, 3.1, 5.6, 3.1, "wake once")
node(ax1, 5.6, 3.1, "H-Mon\n(only awakening)", color="#dbe9f6")

edge(ax1, 2.5, 0.1, 5.6, 0.9, "wake, interview")
node(ax1, 5.6, 0.9, "T-Mon\n(1st awakening)", color="#f6dada")
edge(ax1, 2.5, 0.1, 5.6, -0.7, "memory wiped,\nwake again")
node(ax1, 5.6, -0.7, "T-Tue\n(2nd awakening)", color="#f6dada")

ax1.set_xlim(-1.6, 7.0)
ax1.set_ylim(-1.6, 4.1)
ax1.axis("off")
ax1.set_title("Awakening tree: heads once, tails twice")

# --- right: two ways to count the same tree ---
x_coin = [0, 1]
x_wake = [2.4, 3.4, 4.4]
ax2.bar(x_coin, [0.5, 0.5], width=0.75, color=["#4a7ab5", "#c0504d"])
ax2.bar(x_wake, [1 / 3, 1 / 3, 1 / 3], width=0.75,
        color=["#4a7ab5", "#c0504d", "#c0504d"])
ax2.set_xticks(x_coin + x_wake)
ax2.set_xticklabels(["Heads", "Tails", "H-Mon", "T-Mon", "T-Tue"], fontsize=8.5)
ax2.axhline(0.5, color="0.6", lw=0.8, ls="--")
ax2.axhline(1 / 3, color="0.6", lw=0.8, ls="--")
ax2.set_ylim(0, 0.66)
ax2.set_ylabel("credence assigned to that outcome")
ax2.set_title("Two sample spaces, two answers")
ax2.text(0.5, 0.585, "by coin: P(Heads) = 1/2", ha="center", fontsize=8.6)
ax2.text(3.4, 0.585, "by awakening: P(Heads) = 1/3", ha="center", fontsize=8.6)

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)  # build_figures.py reads this
