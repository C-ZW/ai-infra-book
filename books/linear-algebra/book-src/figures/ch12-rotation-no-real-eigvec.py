# ch12 figure: rotation R(60) turns every direction (no fixed line), while the
# spine S=[[2,1],[1,2]] keeps two lines fixed -- its real eigenvectors (1,1),(1,-1).
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch12-rotation-no-real-eigvec.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

th = np.deg2rad(60.0)
R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])   # R(60), ccw
S = np.array([[2.0, 1.0], [1.0, 2.0]])                                # spine matrix
dirs = np.stack([np.cos(np.linspace(0, np.pi, 12)),                   # a fan of input
                 np.sin(np.linspace(0, np.pi, 12))])                  # directions on a ring

fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.4, 4.8))
for ax, M, title in [(axL, R, "R(60): every arrow turns 60 -- no fixed line"),
                     (axR, S, "S=[[2,1],[1,2]]: two fixed lines stay put")]:
    out = M @ dirs
    for i in range(dirs.shape[1]):                                    # input gray, output blue
        ax.annotate("", xy=dirs[:, i], xytext=(0, 0), arrowprops=dict(color="0.75", width=0.6, headwidth=4))
        ax.annotate("", xy=out[:, i], xytext=(0, 0), arrowprops=dict(color="#2471a3", width=0.9, headwidth=5))
    if M is S:                                                        # mark the real eigen-lines
        for v, lab in [(np.array([1.0, 1.0]), "lambda=3"), (np.array([1.0, -1.0]), "lambda=1")]:
            u = v / np.linalg.norm(v) * 2.6
            ax.plot([-u[0], u[0]], [-u[1], u[1]], color="#c0392b", lw=1.6, ls="--")
            ax.text(u[0] * 0.55, u[1] * 0.55 + 0.18, lab, color="#c0392b", fontsize=8)
    ax.set_title(title, fontsize=9); ax.set_xlim(-2.8, 2.8); ax.set_ylim(-2.8, 2.8)
    ax.set_aspect("equal"); ax.axhline(0, color="0.4", lw=0.6); ax.axvline(0, color="0.4", lw=0.6)
    ax.set_xticks([]); ax.set_yticks([])

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)             # build_figures.py reads this
