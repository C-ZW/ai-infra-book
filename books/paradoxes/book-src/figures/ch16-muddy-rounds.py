"""ch16: n=3 muddy children, round-by-round reveal across m = 1, 2, 3.

Status grid: for each true muddy count m among three children, shows each
child's answer ("unsure" / "MUDDY!") at rounds 1..3; "-" = puzzle already
ended. English labels only (Agg has no CJK glyphs); Chinese walkthrough is
in the chapter text. Output: figures/out/ch16-muddy-rounds.svg
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# scenarios[m] = (who is muddy, rows[child][round] answer or None if ended)
scenarios = {
    1: ("Muddy: Child 3 only", [
        ["unsure", None, None],
        ["unsure", None, None],
        ["MUDDY!", None, None],
    ]),
    2: ("Muddy: Child 2, Child 3", [
        ["unsure", "unsure", None],
        ["unsure", "MUDDY!", None],
        ["unsure", "MUDDY!", None],
    ]),
    3: ("Muddy: Child 1, Child 2, Child 3", [
        ["unsure", "unsure", "MUDDY!"],
        ["unsure", "unsure", "MUDDY!"],
        ["unsure", "unsure", "MUDDY!"],
    ]),
}

fig, axes = plt.subplots(3, 1, figsize=(7.2, 9.2))
for ax, m in zip(axes, (1, 2, 3)):
    ax.axis("off")
    title, rows = scenarios[m]
    ax.set_title(f"True muddy count m={m} -- {title}", fontsize=11, loc="left")
    col_x = [0.30, 0.55, 0.80]
    ax.text(0.04, 0.92, "Child", fontsize=9.5, fontweight="bold")
    for c, x in enumerate(col_x):
        ax.text(x, 0.92, f"Round {c + 1}", fontsize=9.5, fontweight="bold", ha="center")
    ax.plot([0.0, 1.0], [0.80, 0.80], color="black", linewidth=0.8)
    row_y = [0.58, 0.32, 0.06]
    for r, y in enumerate(row_y):
        ax.text(0.04, y, f"Child {r + 1}", fontsize=9.5, va="center")
        for c, x in enumerate(col_x):
            val = rows[r][c]
            if val is None:
                ax.text(x, y, "-", fontsize=9.5, ha="center", va="center", color="#bbbbbb")
            elif val == "MUDDY!":
                ax.text(x, y, val, fontsize=9.5, ha="center", va="center",
                        color="#b3261e", fontweight="bold")
            else:
                ax.text(x, y, val, fontsize=9.5, ha="center", va="center", color="#555555")

fig.suptitle("Muddy Children, n=3: who knows they're muddy, round by round", fontsize=12)
fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.03, hspace=0.55)
out_path = Path(__file__).resolve().parent / "out" / "ch16-muddy-rounds.svg"
out_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out_path, format="svg")
print(f"Saved: {out_path}")
