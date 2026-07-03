# ch27 figure: taxonomy grid, 9 assumption types (rows) x chapters 02-26 (cols).
# A filled dot = the chapter's primary type (the best-fit reading of its own
# "unspoken sentence"). An open circle = a secondary cross-reference (the
# same chapter also brushes a second type). Two columns (ch17, ch22) are
# left with no dot on purpose: those chapters are the book's explicit
# "no accepted solution" cases and sit outside all 9 types -- an empty
# column is itself the point, not a missing data.
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch27-taxonomy.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

types = [
    "ignore conditioning",
    "an action leaks info",
    "mutual != common knowledge",
    "ignore absorbing boundary",
    "EV != price",
    "random / beats undefined",
    "aggregation flips direction",
    "transitivity assumed",
    "non-measurable",
]

chapters = [f"{i:02d}" for i in range(2, 27)]

primary = {
    "05": 0, "06": 0, "08": 0, "11": 0,
    "02": 1, "03": 1, "04": 1,
    "15": 2, "16": 2, "18": 2,
    "10": 3,
    "12": 4, "13": 4,
    "23": 5, "24": 5, "25": 5,
    "07": 6, "09": 6, "14": 6, "21": 6,
    "19": 7, "20": 7,
    "26": 8,
}
secondary = {"13": 8, "19": 5}

fig, ax = plt.subplots(figsize=(14, 6.4))
for j, ch in enumerate(chapters):
    if ch in primary:
        i = primary[ch]
        ax.scatter(j, i, s=140, color=f"C{i}", zorder=3)
    if ch in secondary:
        i = secondary[ch]
        ax.scatter(j, i, s=140, facecolors="none", edgecolors=f"C{i}",
                   linewidths=1.8, zorder=3)

for empty_ch in ("17", "22"):
    j = chapters.index(empty_ch)
    ax.axvspan(j - 0.4, j + 0.4, color="grey", alpha=0.15, zorder=0)

ax.set_xticks(range(len(chapters)))
ax.set_xticklabels([f"ch{c}" for c in chapters], rotation=90, fontsize=8)
ax.set_yticks(range(len(types)))
ax.set_yticklabels(types, fontsize=9.5)
ax.set_xlim(-0.8, len(chapters) - 0.2)
ax.set_ylim(-0.8, len(types) - 0.2)
ax.grid(True, alpha=0.2)
ax.set_title("9 assumption types x chapters 02-26 (open circle = secondary link)",
             fontsize=11)
ax.annotate("ch17, ch22: no dot on purpose -\nno accepted solution, outside the 9 types",
            xy=(chapters.index("17"), 5.3), xytext=(1, 8.0), fontsize=8.2,
            color="#555555", arrowprops=dict(arrowstyle="->", color="#555555"))

fig.tight_layout()
fig.savefig(OUT)
print("wrote", OUT)
