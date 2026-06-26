# ch08 figure: e^{i*theta} on the unit circle, with velocity arrow i*e^{i*theta} (90 deg ahead)
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch08-euler-circle.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(5, 5))
t = np.linspace(0, 2 * np.pi, 400)
ax.plot(np.cos(t), np.sin(t), color="0.7", lw=1.2)        # unit circle
ax.axhline(0, color="0.85"); ax.axvline(0, color="0.85")

# four special angles -> 1, i, -1, -i
marks = [(0, "1"), (np.pi/2, "i"), (np.pi, "-1"), (3*np.pi/2, "-i")]
for ang, lab in marks:
    ax.plot(np.cos(ang), np.sin(ang), "ko", ms=5)
    ax.annotate(lab, (np.cos(ang), np.sin(ang)), textcoords="offset points",
                xytext=(8, 8), fontsize=11)

th = np.pi / 3                                             # the moving point e^{i*theta}, theta=60 deg
px, py = np.cos(th), np.sin(th)
ax.plot([0, px], [0, py], "C0-", lw=2)                    # radius (position vector)
ax.plot(px, py, "C0o", ms=7)
ax.annotate(r"$e^{i\theta}$", (px, py), textcoords="offset points", xytext=(8, -2), color="C0", fontsize=12)
# velocity = i*e^{i*theta} = (-sin, cos): 90 deg ahead, tangent to circle
ax.annotate("", xy=(px - np.sin(th), py + np.cos(th)), xytext=(px, py),
            arrowprops=dict(arrowstyle="->", color="C3", lw=2))
ax.annotate(r"$i\,e^{i\theta}$ (velocity)", (px - np.sin(th), py + np.cos(th)),
            textcoords="offset points", xytext=(4, 6), color="C3", fontsize=11)

ax.set_aspect("equal"); ax.set_xlim(-1.6, 1.6); ax.set_ylim(-1.6, 1.6)
ax.set_xlabel("Re"); ax.set_ylabel("Im")
ax.set_title(r"$e^{i\theta}=\cos\theta+i\sin\theta$: velocity $\perp$ radius")
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
