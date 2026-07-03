# ch04 figure: three Bertrand boxes (GG / GS / SS), six faces total,
# gold faces circled in red so the reader can see which ones share a box.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # headless; no display needed
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

OUT = Path(__file__).resolve().parent / "out" / "ch04-boxes.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

GOLD = "#d4af37"
SILVER = "#b0b3b8"

# each box: (label, bottom_face_color, top_face_color)
boxes = [
    ("Box GG", GOLD, GOLD),
    ("Box GS", GOLD, SILVER),
    ("Box SS", SILVER, SILVER),
]

fig, ax = plt.subplots(figsize=(7.2, 4.4))
w, h, gap = 1.4, 1.0, 0.7

for i, (label, bottom, top) in enumerate(boxes):
    x = i * (w + gap)
    ax.add_patch(mpatches.Rectangle((x, 0), w, h, facecolor=bottom,
                                     edgecolor="black", lw=1.5))
    ax.add_patch(mpatches.Rectangle((x, h), w, h, facecolor=top,
                                     edgecolor="black", lw=1.5))
    ax.text(x + w / 2, -0.4, label, ha="center", fontsize=11)
    # circle every gold face in red so the reader can count them
    if bottom == GOLD:
        ax.add_patch(mpatches.Rectangle((x, 0), w, h, facecolor="none",
                                         edgecolor="firebrick", lw=2.8))
    if top == GOLD:
        ax.add_patch(mpatches.Rectangle((x, h), w, h, facecolor="none",
                                         edgecolor="firebrick", lw=2.8))

ax.text(-0.35, 2.35, "3 gold faces total (circled)", fontsize=9.5, color="firebrick")
ax.text(-0.35, 2.12, "2 of the 3 share a box with another gold face -> 2/3",
        fontsize=9.5, color="firebrick")

ax.set_xlim(-0.6, 3 * (w + gap) - gap + 0.6)
ax.set_ylim(-0.7, 2.6)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("Bertrand's box paradox: 3 boxes, 6 faces, 3 gold")
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
