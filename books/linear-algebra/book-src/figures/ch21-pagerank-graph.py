# ch21 figure: tiny web graph + PageRank steady state, and power-iteration convergence.
# Graph A->B, A->C, B->C, C->A. Column-stochastic M (column j = node j out-links).
# Steady state pi=(0.4,0.2,0.4); node size scales with pi. Right panel: power
# iteration from uniform spirals into pi (lambda2 is complex, |lambda2|=1/sqrt2).
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch21-pagerank-graph.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

M = np.array([[0, 0, 1.], [0.5, 0, 0], [0.5, 1., 0]])      # cols A,B,C sum to 1
pos = {"A": (0, 1.0), "B": (-0.9, -0.6), "C": (0.9, -0.6)}  # node coords
edges = [("A", "B"), ("A", "C"), ("B", "C"), ("C", "A")]    # directed out-links
pi = np.array([0.4, 0.2, 0.4])                              # M pi = pi (verified)

fig, (axg, axc) = plt.subplots(1, 2, figsize=(10, 5))
for s, t in edges:                                          # draw directed arrows
    p, q = np.array(pos[s]), np.array(pos[t])
    axg.annotate("", xy=q*0.78, xytext=p*0.78,
                 arrowprops=dict(arrowstyle="-|>", color="#555", lw=1.4))
for i, (name, (x, y)) in enumerate(pos.items()):            # node size ~ steady prob
    axg.scatter([x], [y], s=6000*pi[i], color="#2471a3", alpha=0.85, zorder=3)
    axg.text(x, y, f"{name}\n{pi[i]:.1f}", ha="center", va="center",
             color="white", fontsize=11, zorder=4)
axg.set_title("web graph: node size ~ PageRank (steady state)", fontsize=10)
axg.set_xlim(-1.6, 1.6); axg.set_ylim(-1.3, 1.5); axg.set_aspect("equal"); axg.axis("off")

p = np.full(3, 1/3)                                         # power iteration from uniform
hist = [p.copy()]
for _ in range(14):
    p = M @ p; p = p / p.sum(); hist.append(p.copy())
hist = np.array(hist)
for i, name in enumerate("ABC"):
    axc.plot(hist[:, i], marker="o", ms=3, label=f"pi_{name}")
for i, val in enumerate(pi):
    axc.axhline(val, color="0.7", ls="--", lw=0.8)
axc.set_title("power iteration from uniform -> (0.4,0.2,0.4)", fontsize=10)
axc.set_xlabel("iteration k"); axc.set_ylabel("probability"); axc.legend(fontsize=8)
axc.grid(True, color="0.92", lw=0.6)
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
