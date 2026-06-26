"""Koch curve generations 0 through 3."""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)


def koch(p1, p2):
    p1 = np.array(p1, float)
    p2 = np.array(p2, float)
    d = (p2 - p1) / 3.0
    a = p1 + d
    b = p1 + 2 * d
    ang = np.deg2rad(60)
    rot = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
    peak = a + rot.dot(b - a)
    return [p1, a, peak, b, p2]


def generation(level):
    pts = [np.array([0.0, 0.0]), np.array([1.0, 0.0])]
    for _ in range(level):
        new = [pts[0]]
        for i in range(len(pts) - 1):
            seg = koch(pts[i], pts[i + 1])
            new += seg[1:]
        pts = new
    return np.array(pts)


fig, axes = plt.subplots(4, 1, figsize=(7.2, 5.6))
for level, ax in enumerate(axes):
    pts = generation(level)
    ax.plot(pts[:, 0], pts[:, 1], color="#1f4e79", lw=1.0)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 0.40)
    ax.text(-0.01, 0.18, "gen %d" % level, fontsize=9, color="#555")
fig.suptitle("Koch curve: each segment becomes four (length grows as (4/3)^n)",
             fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(OUT / "ch12-koch.svg")
print("wrote ch12-koch.svg")
