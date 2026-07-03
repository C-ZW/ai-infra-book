# ch13 figure: two computation trees for the two-envelope argument.
# Left: the naive tree -- claims the SAME two-branch, 50/50 shape for every
# possible observed amount Y, including impossible ones (needs a prior that
# cannot exist). Right: the real tree at the top edge of a bounded, proper
# prior {100, 200, 400} -- only ONE branch is possible, and switching is a
# certain loss even though the naive formula claims a gain.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch13-envelope-tree.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

fig, (axL, axR) = plt.subplots(1, 2, figsize=(12, 5.8))


def node(ax, x, y, text, color="0.92"):
    ax.text(x, y, text, ha="center", va="center", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.32", fc=color, ec="0.35"))


def edge(ax, x0, y0, x1, y1, label, color="0.45"):
    ax.plot([x0, x1], [y0, y1], color=color, lw=1.3, zorder=1)
    ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.16, label, fontsize=8, ha="center", color=color)


# Left: naive tree, same shape claimed for every Y (including Y = 800)
node(axL, 0, 0, "You see Y = 800", color="#eef2f6")
edge(axL, 0, 0, 2.6, 1.3, "assumed 1/2", color="#c0392b")
node(axL, 2.6, 1.3, "other = 1600\n(does not exist!)", color="#f6dada")
edge(axL, 0, 0, 2.6, -1.3, "assumed 1/2", color="#c0392b")
node(axL, 2.6, -1.3, "other = 400", color="#f6dada")
axL.text(1.3, -2.5, "naive formula: E[other] = 1.25 x 800 = 1000\n(claims a +200 gain)",
         fontsize=8.6, ha="center", color="#c0392b")
axL.set_xlim(-1.6, 5.2)
axL.set_ylim(-3.2, 2.4)
axL.axis("off")
axL.set_title("config 1: naive tree (same shape for every Y)", fontsize=10)

# Right: real tree under bounded proper prior {100, 200, 400}, at the top edge
node(axR, 0, 0, "You see Y = 800", color="#eef2f6")
edge(axR, 0, 0, 2.8, 0, "posterior = 1\n(only tier a=400 fits)", color="#2b6cb0")
node(axR, 2.8, 0, "other = 400\n(certain)", color="#dbf6df")
axR.text(1.4, -1.6, "true E[other] = 400  ->  gain = -400\n(the top of the ladder has no room above it)",
         fontsize=8.6, ha="center", color="#2b6cb0")
axR.set_xlim(-1.6, 5.2)
axR.set_ylim(-3.2, 2.4)
axR.axis("off")
axR.set_title("config 2: real tree at the edge of prior {100,200,400}", fontsize=10)

fig.suptitle("Two envelopes: a tree assumed to always fork vs. a tree that runs out of room", fontsize=11)
fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
