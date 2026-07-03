# ch24 figure: Bertrand's chord paradox, three constructions side by side.
# Endpoints -> 120-degree arc; radius -> near half of a radius;
# midpoint -> concentric disk of radius R/2 (area 1/4 of the whole disk).
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless; no display needed
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

OUT = Path(__file__).resolve().parent / "out" / "ch24-bertrand-chord.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

R = 1.0
GREEN = "#2e7d32"
RED = "#c62828"
GREY = "#8a8a8a"

def base_circle(ax):
    ax.add_patch(mpatches.Circle((0, 0), R, fill=False, edgecolor="black", lw=1.3))
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.set_aspect("equal")
    ax.axis("off")

fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.6))

# vertices of the inscribed equilateral triangle at 90, 210, 330 degrees
angs = np.deg2rad([90, 210, 330])
tri = np.column_stack([R * np.cos(angs), R * np.sin(angs)])

# Panel 1: random endpoints -> the arc BC (not containing A) is the win zone
ax = axes[0]
base_circle(ax)
ax.add_patch(mpatches.Polygon(tri, closed=True, fill=False, edgecolor=GREY, lw=1.0, ls="--"))
ax.add_patch(mpatches.Arc((0, 0), 2 * R, 2 * R, angle=0, theta1=210, theta2=330, color=GREEN, lw=6))
ax.plot(*tri[0], "ko", ms=5)
ax.text(tri[0][0], tri[0][1] + 0.14, "A", ha="center")
ax.set_title("random endpoints\nP = 1/3 (120-degree arc)")

# Panel 2: random radius -> the near half of the radius is the win zone
ax = axes[1]
base_circle(ax)
ax.plot([0, 0], [0, R / 2], color=GREEN, lw=5)
ax.plot([0, 0], [R / 2, R], color=RED, lw=5)
half_w = np.sqrt(R ** 2 - (R / 2) ** 2)
ax.plot([-half_w, half_w], [R / 2, R / 2], color="black", lw=1, ls="--")
ax.set_title("random radius\nP = 1/2 (near half of radius)")

# Panel 3: random midpoint -> inner disk of radius R/2 is the win zone
ax = axes[2]
base_circle(ax)
ax.add_patch(mpatches.Circle((0, 0), R, facecolor=RED, alpha=0.25, edgecolor="none"))
ax.add_patch(mpatches.Circle((0, 0), R / 2, facecolor=GREEN, alpha=0.6, edgecolor="black", lw=1))
ax.set_title("random midpoint\nP = 1/4 (inner disk area)")

fig.suptitle("Bertrand's chord paradox: same question, three constructions, three answers")
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
