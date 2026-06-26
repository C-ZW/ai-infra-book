# ch03 figure: unit circle with sin/cos/tan/sec drawn as colored line segments
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch03-unit-circle-six.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

theta = np.deg2rad(50)         # the one angle we illustrate (try 30, 60, 110, -40)
c, s = np.cos(theta), np.sin(theta)
t = np.tan(theta)              # tangent-segment height on the line x=1
fig, ax = plt.subplots(figsize=(6, 6))

# unit circle + axes
ang = np.linspace(0, 2 * np.pi, 400)
ax.plot(np.cos(ang), np.sin(ang), color="0.6", lw=1)
ax.axhline(0, color="0.8", lw=0.8); ax.axvline(0, color="0.8", lw=0.8)
ax.plot([1, 1], [-1.6, 1.6], color="0.85", lw=1, ls="--")  # tangent line x=1

# segments: cos (x-shadow), sin (y-shadow), tan (on x=1), sec (O to T)
ax.plot([0, c], [0, 0], color="tab:blue", lw=3, label=f"cos = {c:.3f}")
ax.plot([c, c], [0, s], color="tab:red", lw=3, label=f"sin = {s:.3f}")
ax.plot([1, 1], [0, t], color="tab:green", lw=3, label=f"tan = {t:.3f}")
ax.plot([0, 1], [0, t], color="tab:purple", lw=2, ls="-", label=f"sec = {1/c:.3f}")
ax.plot([0, c], [0, s], color="black", lw=1.5)             # radius OP
ax.plot([c], [s], "ko", ms=5)
ax.annotate("P=(cos, sin)", (c, s), textcoords="offset points", xytext=(6, 6))
ax.annotate("T", (1, t), textcoords="offset points", xytext=(6, 0))

# quadrant-sign inset: (cos, sin) signs per quadrant
signs = [("+,+", 0.5, 0.5), ("-,+", -0.5, 0.5), ("-,-", -0.5, -0.5), ("+,-", 0.5, -0.5)]
for txt, x, y in signs:
    ax.text(x, y, txt, ha="center", va="center", fontsize=8, color="0.4")

ax.set_xlim(-1.4, 1.8); ax.set_ylim(-1.4, 1.8)
ax.set_aspect("equal")         # keep the circle round
ax.legend(loc="lower left", fontsize=8); ax.set_title("Six functions as segments (theta=50 deg)")
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
