# ch07 figure: two pictures of S x = (3,0). Left = row picture (two lines meet
# at (2,-1)). Right = column picture: b=(3,0) = 2*(2,1) + (-1)*(1,2), drawn tip-to-tail.
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch07-row-vs-column.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

fig, (axL, axR) = plt.subplots(1, 2, figsize=(10.5, 5.2))

# --- left: row picture. Lines 2x+y=3 and x+2y=0, meeting at (2,-1) ---
x = np.linspace(-1, 4, 50)
axL.plot(x, 3 - 2 * x, color="#2471a3", lw=2, label="2x + y = 3  (row 1)")
axL.plot(x, -x / 2, color="#e07b39", lw=2, label="x + 2y = 0  (row 2)")
axL.plot(2, -1, "o", color="#c0392b", ms=9)
axL.text(2.1, -1.05, "(2, -1)", color="#c0392b", fontsize=10)
axL.set_title("row picture: lines meet at the solution", fontsize=10)
axL.set_xlim(-1, 4); axL.set_ylim(-2.5, 3.5); axL.legend(fontsize=8, loc="upper right")

# --- right: column picture. b = 2*c1 + (-1)*c2, tip-to-tail ---
c1 = np.array([2.0, 1.0]); c2 = np.array([1.0, 2.0]); b = 2 * c1 - 1 * c2  # = (3,0)
axR.annotate("", xy=2 * c1, xytext=(0, 0), arrowprops=dict(color="#2471a3", width=2, headwidth=9))
axR.annotate("", xy=b, xytext=2 * c1, arrowprops=dict(color="#e07b39", width=2, headwidth=9))
axR.annotate("", xy=b, xytext=(0, 0), arrowprops=dict(color="#c0392b", width=2.4, headwidth=11))
axR.text(2.0, 2.2, "2*(2,1)", color="#2471a3", fontsize=9)
axR.text(3.2, 1.1, "-1*(1,2)", color="#e07b39", fontsize=9)
axR.text(1.4, -0.45, "b = (3,0)", color="#c0392b", fontsize=10)
axR.set_title("column picture: 2*c1 + (-1)*c2 = b", fontsize=10)
axR.set_xlim(-1, 5); axR.set_ylim(-1.5, 3.5)

for ax in (axL, axR):
    ax.set_aspect("equal"); ax.axhline(0, color="0.6", lw=0.6); ax.axvline(0, color="0.6", lw=0.6)
fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)             # build_figures.py reads this
