# ch10 figure: a rotating phasor (left) and its vertical projection unrolled into a sine wave (right)
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch10-phasor-to-wave.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

A, w, phi = 1.0, 1.0, np.pi / 6        # amplitude, angular freq, initial phase
t_now = 0.9                            # the "current" time we draw the arrow at
ang = w * t_now + phi                  # current arrow angle = w*t + phi

fig, (axL, axR) = plt.subplots(1, 2, figsize=(9, 4.2),
                               gridspec_kw={"width_ratios": [1, 1.6]})
# --- left: rotating phasor on a circle ---
th = np.linspace(0, 2 * np.pi, 200)
axL.plot(A * np.cos(th), A * np.sin(th), color="0.7", lw=1)          # circle radius A
axL.annotate("", xy=(A * np.cos(ang), A * np.sin(ang)), xytext=(0, 0),
             arrowprops=dict(arrowstyle="->", color="C0", lw=2))     # the phasor arrow
axL.plot([A * np.cos(ang)] * 2, [0, A * np.sin(ang)], "--", color="0.5", lw=1)  # drop to its height
axL.text(0.30 * np.cos(ang / 2), 0.30 * np.sin(ang / 2), "wt+phi", fontsize=9)
axL.text(A * np.cos(ang) * 0.55, A * np.sin(ang) * 0.55 + 0.06, "A", color="C0", fontsize=10)
axL.set_aspect("equal"); axL.set_xlim(-1.3, 1.3); axL.set_ylim(-1.3, 1.3)
axL.axhline(0, color="0.85"); axL.axvline(0, color="0.85")
axL.set_title("phasor: A*e^{i(wt+phi)}"); axL.set_xlabel("Re"); axL.set_ylabel("Im")
# --- right: vertical coordinate unrolled over time = sine wave ---
t = np.linspace(0, 4 * np.pi, 400)
axR.plot(t, A * np.sin(w * t + phi), color="C0", lw=2)              # the wave
axR.plot([0, t_now], [A * np.sin(ang)] * 2, "--", color="0.5", lw=1)  # link same height
axR.plot(t_now, A * np.sin(ang), "o", color="C3")                  # corresponding point
axR.axhline(0, color="0.85")
axR.set_title("its vertical shadow over time = A*sin(wt+phi)")
axR.set_xlabel("t"); axR.set_ylabel("y"); axR.set_ylim(-1.3, 1.3)
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
