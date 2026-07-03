# ch15 figure: two panels.
# Left: departure day d equals blue-eyed count k, a staircase extended to
# k=100 (base number B11: 100 blue-eyed islanders leave on day 100).
# Right: a knowledge-order ladder for a small illustrative k=4 -- orders
# 0..k-1 already hold as mutual knowledge before the announcement; only
# order k (and everything above it) is missing until the public statement
# supplies it, which is exactly what closes the induction.
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch15-induction-days.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 5))

# --- left panel: d = k staircase out to k = 100 ---
ks = list(range(1, 101))
ax1.step(ks, ks, where="mid", color="#1f5fa8", linewidth=1.6)
marks = [1, 2, 3, 10, 50, 100]
for k in marks:
    ax1.plot([k], [k], marker="o", color="#c0392b", markersize=6, zorder=5)
    ax1.annotate(f"k={k}\nday {k}", xy=(k, k), xytext=(k + 2, k - 14),
                 fontsize=8, color="#c0392b")
ax1.set_xlabel("number of blue-eyed islanders, k")
ax1.set_ylabel("day everyone departs, d")
ax1.set_title("Departure day d = k (B11: k=100 -> day 100)")
ax1.set_xlim(0, 108)
ax1.set_ylim(0, 108)
ax1.grid(True, alpha=0.25)

# --- right panel: knowledge-order ladder for a demo k=4 ---
k_demo = 4
ax2.set_xlim(0, 10)
ax2.set_ylim(-0.5, k_demo + 2.2)
ax2.axis("off")
for order in range(0, k_demo + 1):
    held_already = order < k_demo
    color = "#1e7d32" if held_already else "#c0392b"
    tag = "already mutual knowledge" if held_already else "missing until announcement"
    ax2.barh(order, 8.2, height=0.65, color=color, alpha=0.8)
    ax2.text(0.15, order, f"order {order}: {tag}", va="center",
              fontsize=8.5, color="white")
ax2.annotate("public announcement fills order k\nand every order above it, at once",
             xy=(4.1, k_demo), xytext=(0.8, k_demo + 1.6),
             arrowprops=dict(arrowstyle="->", color="black"), fontsize=9)
ax2.set_title(f"Knowledge-order ladder, demo k={k_demo}")

fig.tight_layout()
fig.savefig(OUT)
print("wrote", OUT)
