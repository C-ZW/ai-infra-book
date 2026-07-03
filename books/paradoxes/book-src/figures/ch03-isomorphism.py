"""ch03: Three Prisoners <-> Monty Hall correspondence table.

Renders a row-by-row mapping between the Three Prisoners problem and the
Monty Hall problem, highlighting the two odds rows (1/3 stays, 2/3 shifts)
that are numerically identical in both stories. Labels are kept in English
(matplotlib's default Agg font has no CJK glyphs); the Chinese explanation
lives in the chapter text around the embedded image.

Output: figures/out/ch03-isomorphism.svg
"""
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = [
    ("Random assignment", "Warden knows who is pardoned (1/3 each)", "Host knows which door hides the car (1/3 each)"),
    ("Your fixed position", "Prisoner A (the one who asks)", "The door you first picked"),
    ("The informed third party", "The warden", "The host"),
    ("Constrained statement", "Must name B or C as doomed,\nnever A", "Must open a goat door,\nnever the one you picked"),
    ("Tie-break rule", "If A is pardoned, coin-flip\nbetween naming B or C", "If you picked the car, coin-flip\nbetween the two goat doors"),
    ("The un-named alternative", "Prisoner C", "The other unopened door"),
    ("Stay probability", "A survives = 1/3 (unchanged)", "Stick with pick = 1/3 (unchanged)"),
    ("Switch probability", "C survives = 2/3 (rises)", "Switch = 2/3 (rises)"),
]

fig, ax = plt.subplots(figsize=(10.5, 7.2))
ax.axis("off")

col_x = [0.02, 0.32, 0.68]
headers = ["Correspondence", "Three Prisoners", "Monty Hall"]
header_y = 0.965
for x, h in zip(col_x, headers):
    ax.text(x, header_y, h, fontsize=12, fontweight="bold", va="top")
ax.plot([0.02, 0.985], [0.935, 0.935], color="black", linewidth=1.1)

n = len(rows)
top, bottom = 0.90, 0.02
step = (top - bottom) / n
for i, (label, prisoners, monty) in enumerate(rows):
    y = top - i * step
    is_odds_row = i >= n - 2
    color = "#b3261e" if is_odds_row else "black"
    weight = "bold" if is_odds_row else "normal"
    ax.text(col_x[0], y, label, fontsize=10.5, va="top", color=color, fontweight=weight)
    ax.text(col_x[1], y, prisoners, fontsize=9.5, va="top", color=color, fontweight=weight)
    ax.text(col_x[2], y, monty, fontsize=9.5, va="top", color=color, fontweight=weight)
    if i < n - 1:
        ax.plot([0.02, 0.985], [y - step + 0.012, y - step + 0.012],
                 color="#dddddd", linewidth=0.6)

ax.set_title("Three Prisoners <-> Monty Hall: item-by-item isomorphism", fontsize=13, pad=14)
fig.tight_layout()

out_path = Path(__file__).resolve().parent / "out" / "ch03-isomorphism.svg"
out_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out_path, format="svg")
print(f"Saved: {out_path}")
