# ch05 figure: one asymmetric arrow shown original, rotated 30 deg, then +60 deg (total 90)
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch05-rotation-compose.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

def R(deg):                                    # 2D rotation matrix, ccw positive
    t = np.radians(deg)
    return np.array([[np.cos(t), -np.sin(t)],
                     [np.sin(t),  np.cos(t)]])

# an asymmetric arrow as a polyline (shaft + two head barbs), pointing +x
arrow = np.array([[0, 0], [1.0, 0], [0.75, 0.12], [1.0, 0], [0.75, -0.12]]).T

fig, ax = plt.subplots(figsize=(5, 5))
for deg, color, lab in [(0, "0.6", "original 0 deg"),
                        (30, "C0", "R(30)"),
                        (90, "C3", "R(30)R(60) = R(90)")]:
    p = R(deg) @ arrow                         # rotate every point
    ax.plot(p[0], p[1], color=color, lw=2.5, label=lab)

# arc annotation: show the 30 then 60 split summing to 90
arc = np.linspace(0, np.pi / 2, 60)
ax.plot(0.45 * np.cos(arc), 0.45 * np.sin(arc), "k--", lw=0.8)
ax.text(0.5, 0.18, "30", color="C0"); ax.text(0.2, 0.42, "+60", color="C3")
ax.axhline(0, color="0.85"); ax.axvline(0, color="0.85")
ax.set_aspect("equal")                         # keep angles honest
ax.set_xlim(-0.4, 1.2); ax.set_ylim(-0.4, 1.2)
ax.legend(loc="lower left", fontsize=8)
ax.set_title("Rotations compose: 30 then 60 = 90")
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
