"""ch19: The Efron dice cycle A -> B -> C -> D -> A, each edge winning 2/3.

Four dice are placed at the corners of a square. Solid arrows trace the
main cycle (A beats B, B beats C, C beats D, D beats A), each labeled 2/3.
The two diagonals of the square are exactly the two non-adjacent pairs:
C vs A (the exception, 5/9, dashed) and B vs D (an even 1/2, dotted).
This makes the "two diagonals are different from each other, and neither
is 2/3" landmine a visual fact, not just a sentence.

Output: figures/out/ch19-nontransitive-cycle.svg
"""
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6.2, 6.2))
ax.set_xlim(-0.4, 1.4)
ax.set_ylim(-0.4, 1.4)
ax.set_aspect("equal")
ax.axis("off")

pos = {"A": (0, 1), "B": (1, 1), "C": (1, 0), "D": (0, 0)}
cycle_edges = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")]

for name, (x, y) in pos.items():
    ax.scatter([x], [y], s=2200, color="#2b6cb0", zorder=3)
    ax.text(x, y, name, color="white", fontsize=22, ha="center", va="center",
            zorder=4, fontweight="bold")

for src, dst in cycle_edges:
    x0, y0 = pos[src]
    x1, y1 = pos[dst]
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color="#1a202c", lw=2.6,
                                 shrinkA=30, shrinkB=30,
                                 connectionstyle="arc3,rad=0.14"))
    mx, my = (x0 + x1) / 2 + 0.06, (y0 + y1) / 2 + 0.06
    ax.text(mx, my, "2/3", fontsize=13, color="#c53030", ha="center", va="center",
            fontweight="bold", bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))

ax.annotate("", xy=pos["A"], xytext=pos["C"],
            arrowprops=dict(arrowstyle="-|>", color="#dd6b20", lw=2.0, linestyle="dashed",
                             shrinkA=32, shrinkB=32))
ax.text(0.5, 0.58, "C beats A = 5/9\n(exception, not 2/3)", fontsize=10.5, color="#dd6b20",
        ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.2", fc="#fffaf0", ec="#dd6b20"))

ax.plot([pos["B"][0], pos["D"][0]], [pos["B"][1], pos["D"][1]],
        linestyle="dotted", color="#718096", lw=1.8, zorder=1)
ax.text(0.5, 0.34, "B vs D = 1/2 (even)", fontsize=10, color="#4a5568", ha="center", va="center")

ax.set_title("Efron dice: cycle A-B-C-D-A each 2/3, diagonals differ", fontsize=11.5, pad=12)
fig.tight_layout()

out_path = Path(__file__).resolve().parent / "out" / "ch19-nontransitive-cycle.svg"
out_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out_path, format="svg")
print(f"Saved: {out_path}")
