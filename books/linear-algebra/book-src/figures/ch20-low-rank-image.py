# ch20 figure: low-rank image compression. One grayscale image = one matrix.
# Keep only the top-k singular values (truncated SVD) and rebuild: the outline
# emerges as k grows. Each panel prints k and the retained energy ratio
# (sum of top-k sigma^2 / sum of all sigma^2). Eckart-Young: this truncation is
# the BEST rank-k approximation in Frobenius norm. All labels in English.
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch20-low-rank-image.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

np.random.seed(0)                                  # deterministic image
N = 48
img = np.zeros((N, N))
xx, yy = np.meshgrid(np.arange(N), np.arange(N))
img += 0.30 * (((xx // 6) + (yy // 6)) % 2)        # checkerboard texture (raises rank)
img[8:40, 10:15] = 1.0                             # letter 'R': left stem
img[8:13, 10:30] = 1.0                             # top bar
img[20:25, 10:30] = 1.0                            # middle bar
img[8:25, 28:33] = 1.0                             # upper-right vertical
for i in range(16):                                # diagonal leg
    img[24 + i, 18 + i:23 + i] = 1.0
img = np.clip(img + 0.08 * np.random.rand(N, N), 0, 1)

U, s, Vt = np.linalg.svd(img, full_matrices=False)  # img = U @ diag(s) @ Vt
total = (s ** 2).sum()
ks = [1, 2, 5, 16, len(s)]                          # last = full rank (exact)

fig, axes = plt.subplots(1, len(ks), figsize=(15, 3.2))
for ax, k in zip(axes, ks):
    rebuilt = (U[:, :k] * s[:k]) @ Vt[:k]           # best rank-k approximation
    energy = (s[:k] ** 2).sum() / total
    ax.imshow(rebuilt, cmap="gray", vmin=0, vmax=1)
    tag = "k=%d (full)" % k if k == len(s) else "k=%d" % k
    ax.set_title("%s\nenergy %.1f%%" % (tag, energy * 100), fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])
fig.suptitle("Truncated SVD: the outline emerges as k grows (Eckart-Young best rank-k)", fontsize=11)
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
