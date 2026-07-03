"""ch01: The three-step dissection of a paradox.

Renders the book's spine as a flow diagram: Step 1 (confident intuitive
answer) -> Step 2 (the unspoken assumption that made it feel obvious) ->
Step 3 (rigorous rebuild once the assumption is named). A dashed bracket
marks the "gap" between Step 1 and Step 3 as the paradox itself. Labels
are kept in English (matplotlib's default Agg font has no CJK glyphs);
the Chinese explanation lives in the chapter text around the embedded
image.

Output: figures/out/ch01-anatomy.svg
"""
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(10.5, 5.4))
ax.axis("off")
ax.set_xlim(0, 10.5)
ax.set_ylim(0, 5.4)

boxes = [
    (0.6, "Step 1\nConfident intuition", "\"Obviously 1/2\"\n(feels self-evident)", "#c0392b"),
    (4.05, "Step 2\nUnspoken assumption", "Name the smuggled\npremise out loud", "#b7791f"),
    (7.5, "Step 3\nRigorous rebuild", "Recompute under the\ncorrected premise", "#2471a3"),
]
w, h, y0 = 2.85, 1.7, 2.5

for x, title, sub, color in boxes:
    box = FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0.08,rounding_size=0.12",
                          linewidth=1.8, edgecolor=color, facecolor=color + "18")
    ax.add_patch(box)
    ax.text(x + w / 2, y0 + h - 0.42, title, ha="center", va="top",
            fontsize=11.5, fontweight="bold", color=color)
    ax.text(x + w / 2, y0 + h - 1.05, sub, ha="center", va="top", fontsize=9, color="0.2")

arrow_style = dict(arrowstyle="-|>", mutation_scale=22, color="0.25", linewidth=1.6)
for (x1, _, _, _), (x2, _, _, _) in zip(boxes[:-1], boxes[1:]):
    ax.add_patch(FancyArrowPatch((x1 + w + 0.02, y0 + h / 2), (x2 - 0.02, y0 + h / 2), **arrow_style))
ax.text(boxes[0][0] + w + (boxes[1][0] - boxes[0][0] - w) / 2, y0 + h / 2 + 0.28,
        "look for the gap", ha="center", fontsize=8.5, style="italic", color="0.3")
ax.text(boxes[1][0] + w + (boxes[2][0] - boxes[1][0] - w) / 2, y0 + h / 2 + 0.28,
        "fix the premise", ha="center", fontsize=8.5, style="italic", color="0.3")

# dashed bracket spanning Step 1 -> Step 3: the paradox is the distance between them
bx1, bx2, by = boxes[0][0] + w / 2, boxes[2][0] + w / 2, y0 - 0.35
ax.plot([bx1, bx1, bx2, bx2], [by + 0.15, by, by, by + 0.15], linestyle="--", color="0.4", linewidth=1.2)
ax.text((bx1 + bx2) / 2, by - 0.35, "the paradox = the distance intuition never saw",
        ha="center", fontsize=10, color="0.25")

ax.set_title("Anatomy of a paradox: three steps, one hidden premise", fontsize=13, pad=12)
fig.tight_layout()

out_path = Path(__file__).resolve().parent / "out" / "ch01-anatomy.svg"
out_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out_path, format="svg")
print(f"Saved: {out_path}")
