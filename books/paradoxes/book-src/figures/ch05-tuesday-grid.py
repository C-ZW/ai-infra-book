# ch05 figure: 14x14 grid of (child A type, child B type), each type in
# {Boy,Girl} x {Mon..Sun}. Highlights the 27 cells where "at least one
# child is a Boy born on Tuesday" holds, and the 13 of those 27 that are
# also both-boys (BB) -- the 13/27 result worked out in the chapter text.
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")           # headless; no display needed
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

OUT = Path(__file__).resolve().parent / "out" / "ch05-tuesday-grid.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
labels = days + days                       # index 0-6 = Boy, 7-13 = Girl
row = np.arange(14).reshape(14, 1)
col = np.arange(14).reshape(1, 14)

is_boy_tue = 1                              # index 1 within each 7-block = Tue
match = (row == is_boy_tue) | (col == is_boy_tue)     # >=1 child is Boy-Tue
both_boys = (row <= 6) & (col <= 6)

categ = np.zeros((14, 14), dtype=int)
categ[match] = 1                            # matches condition, but not BB
categ[match & both_boys] = 2                # matches condition AND both boys

fig, ax = plt.subplots(figsize=(7.6, 7.6))
cmap = ListedColormap(["#f0f0f0", "#ffdd77", "#d9483d"])
ax.imshow(categ, cmap=cmap, vmin=0, vmax=2)

ax.set_xticks(np.arange(-0.5, 14, 1), minor=True)
ax.set_yticks(np.arange(-0.5, 14, 1), minor=True)
ax.grid(which="minor", color="white", linewidth=1.0)
ax.axhline(6.5, color="black", linewidth=1.8)   # boy/girl block boundary
ax.axvline(6.5, color="black", linewidth=1.8)

ax.set_xticks(range(14)); ax.set_xticklabels(labels, rotation=90, fontsize=7)
ax.set_yticks(range(14)); ax.set_yticklabels(labels, fontsize=7)
ax.set_xlabel("child B: gender-block (Boy | Girl) x day of week", fontsize=9)
ax.set_ylabel("child A: gender-block (Boy | Girl) x day of week", fontsize=9)
ax.text(3, -1.9, "BOY", ha="center", fontsize=10, fontweight="bold")
ax.text(10, -1.9, "GIRL", ha="center", fontsize=10, fontweight="bold")
ax.text(-2.6, 3, "BOY", va="center", rotation=90, fontsize=10, fontweight="bold")
ax.text(-2.6, 10, "GIRL", va="center", rotation=90, fontsize=10, fontweight="bold")

ax.set_title("196 equally likely two-child type-pairs: who counts as \"a Boy-Tuesday\"?", fontsize=10)
legend = [
    Patch(color="#f0f0f0", label="excluded: no Boy-Tue child"),
    Patch(color="#ffdd77", label="matches condition, not both boys (14 cells)"),
    Patch(color="#d9483d", label="matches condition AND both boys (13 cells) -> 13/27"),
]
ax.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, -0.16), fontsize=8, frameon=False)
fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
