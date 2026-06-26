"""Koch curve, generations 0..4 stacked. Pure vector."""
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out"; OUT.mkdir(exist_ok=True)
BG, INK = "#fdfcf9", "#16324f"

def koch(p1, p2, depth):
    if depth == 0:
        return [p1, p2]
    p1, p2 = np.array(p1, float), np.array(p2, float)
    a = p1 + (p2 - p1) / 3
    b = p1 + 2 * (p2 - p1) / 3
    ang = np.deg2rad(-60)
    rot = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
    peak = a + rot @ (b - a)
    pts = []
    for s, e in [(p1, a), (a, peak), (peak, b), (b, p2)]:
        seg = koch(s, e, depth - 1)
        pts += seg[:-1]
    pts.append(p2)
    return pts

fig, ax = plt.subplots(figsize=(7.0, 4.2))
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
for d in range(5):
    pts = np.array(koch((0, 0), (1, 0), d))
    ax.plot(pts[:, 0], pts[:, 1] - 0.42 * d, color=INK, lw=1.1)
    ax.text(-0.05, -0.42 * d, f"gen {d}", color=INK, fontsize=9, ha="right", va="bottom")
ax.set_title("Koch curve: each step replaces a segment by 4 of 1/3 length  (length ×4/3)",
             color=INK, fontsize=10)
ax.set_aspect("equal"); ax.axis("off")
fig.tight_layout()
fig.savefig(OUT / "ch12-koch.svg", facecolor=BG, bbox_inches="tight")
print("ok ch12-koch")
