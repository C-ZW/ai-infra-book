# ch07 figure: complex multiplication = arguments add + moduli multiply; inset of x i four times
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch07-complex-mult.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

z1 = 1 + 1j                     # |z1|=sqrt2, arg 45 deg
z2 = np.sqrt(3) + 1j           # |z2|=2,     arg 30 deg
z3 = z1 * z2                    # |z3|=2sqrt2, arg 75 deg

fig, ax = plt.subplots(figsize=(5.6, 5))
for z, c, lab in [(z1, "C0", "z1 (|z|=√2, arg 45°)"),
                  (z2, "C2", "z2 (|z|=2, arg 30°)"),
                  (z3, "C3", "z1·z2 (|z|=2√2, arg 75°)")]:
    ax.annotate("", xy=(z.real, z.imag), xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color=c, lw=2))
    ax.text(z.real + 0.05, z.imag + 0.05, lab, color=c, fontsize=7)
arc = np.linspace(0, np.deg2rad(75), 80)      # show arguments stacking 0..75
ax.plot(0.6 * np.cos(arc), 0.6 * np.sin(arc), "k--", lw=0.7)
ax.axhline(0, color="0.85"); ax.axvline(0, color="0.85")
ax.set_aspect("equal"); ax.set_xlim(-0.6, 3.0); ax.set_ylim(-0.6, 3.0)
ax.set_xlabel("Re"); ax.set_ylabel("Im")
ax.set_title("Multiply: moduli ×, arguments +")

ins = ax.inset_axes([0.60, 0.60, 0.38, 0.38])  # x i four times: 1 -> i -> -1 -> -i -> 1
for k, c in zip(range(4), ["C0", "C1", "C2", "C3"]):
    p = 1j ** k                                 # i^0,i^1,i^2,i^3
    ins.annotate("", xy=(p.real, p.imag), xytext=(0, 0),
                 arrowprops=dict(arrowstyle="->", color=c, lw=1.5))
ins.set_aspect("equal"); ins.set_xlim(-1.3, 1.3); ins.set_ylim(-1.3, 1.3)
ins.set_xticks([]); ins.set_yticks([]); ins.set_title("× i, four times", fontsize=7)
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
