# ch12 figure: left = beats waveform with slow envelope; right = three Lissajous panels (1:1, 1:2, 2:3)
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch12-beats-lissajous.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

fig = plt.figure(figsize=(10, 4))

# --- left (spans both rows): beats = sin(w1 t) + sin(w2 t), with slow envelope ---
axL = fig.add_subplot(1, 2, 1)
w1, w2 = 1.0, 1.1                                     # two close angular frequencies
t = np.linspace(0, 140, 4000)
axL.plot(t, np.sin(w1 * t) + np.sin(w2 * t), color="0.55", lw=0.8)  # superposed wave
env = 2 * np.cos((w1 - w2) / 2 * t)                  # slow envelope +-2 cos((w1-w2)t/2)
axL.plot(t, env, color="C3", lw=1.6); axL.plot(t, -env, color="C3", lw=1.6)
axL.set_title("Beats: sin(t) + sin(1.1 t)")
axL.set_xlabel("t"); axL.set_ylabel("amplitude")

# --- right column: three Lissajous panels x=sin(a t), y=sin(b t + delta) ---
ratios = [(1, 1, np.pi / 4), (1, 2, np.pi / 2), (2, 3, np.pi / 2)]
tt = np.linspace(0, 2 * np.pi, 2000)
for k, (a, b, d) in enumerate(ratios):
    ax = fig.add_subplot(3, 2, 2 * k + 2)            # right column, three stacked rows
    ax.plot(np.sin(a * tt), np.sin(b * tt + d), color="C0", lw=1.2)
    ax.set_title(f"{a}:{b}", fontsize=9)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
