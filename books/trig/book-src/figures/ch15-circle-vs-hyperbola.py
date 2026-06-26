# ch15 figure: circle (cos t,sin t) vs hyperbola (cosh t,sinh t), both swept by area t/2; inset catenary y=cosh x
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless; no display needed
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out" / "ch15-circle-vs-hyperbola.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

t = 1.1                                                  # the shared parameter (NOT an angle on the right)
fig, (axc, axh) = plt.subplots(1, 2, figsize=(10, 5))

# --- left: unit circle x^2+y^2=1, point (cos t, sin t), shaded sector has area t/2 ---
th = np.linspace(0, 2 * np.pi, 400)
axc.plot(np.cos(th), np.sin(th), color="0.4")            # the circle
s = np.linspace(0, t, 60)                                # sector boundary 0..t
axc.fill(np.concatenate([[0], np.cos(s)]), np.concatenate([[0], np.sin(s)]), color="tab:blue", alpha=0.3)
axc.plot([0, np.cos(t)], [0, np.sin(t)], color="tab:blue")
axc.plot(np.cos(t), np.sin(t), "o", color="tab:blue")
axc.annotate(r"$(\cos t,\ \sin t)$", (np.cos(t), np.sin(t)), textcoords="offset points", xytext=(8, 6))
axc.set_title(r"circle  $x^2+y^2=1$   (area $=t/2$)")
axc.set_aspect("equal"); axc.set_xlim(-1.3, 1.6); axc.set_ylim(-1.3, 1.3)
axc.axhline(0, color="0.8", lw=0.6); axc.axvline(0, color="0.8", lw=0.6)

# --- right: unit hyperbola x^2-y^2=1 (right branch), point (cosh t, sinh t), shaded sector area t/2 ---
u = np.linspace(-1.6, 1.6, 400)
axh.plot(np.cosh(u), np.sinh(u), color="0.4")            # right branch
s = np.linspace(0, t, 60)
axh.fill(np.concatenate([[0], np.cosh(s)]), np.concatenate([[0], np.sinh(s)]), color="tab:red", alpha=0.3)
axh.plot([0, np.cosh(t)], [0, np.sinh(t)], color="tab:red")
axh.plot(np.cosh(t), np.sinh(t), "o", color="tab:red")
axh.annotate(r"$(\cosh t,\ \sinh t)$", (np.cosh(t), np.sinh(t)), textcoords="offset points", xytext=(8, 6))
axh.set_title(r"hyperbola  $x^2-y^2=1$   (area $=t/2$)")
axh.set_aspect("equal"); axh.set_xlim(-0.3, 3.0); axh.set_ylim(-2.2, 2.2)
axh.axhline(0, color="0.8", lw=0.6); axh.axvline(0, color="0.8", lw=0.6)

# --- inset: catenary y=cosh x (a hanging chain), NOT a parabola ---
ins = axh.inset_axes([0.58, 0.06, 0.4, 0.34])
xc = np.linspace(-1.8, 1.8, 200)
ins.plot(xc, np.cosh(xc), color="tab:red")
ins.plot(xc, 1 + xc**2 / 2, "--", color="0.6")          # parabola for contrast
ins.set_title(r"$y=\cosh x$ (chain)", fontsize=8)
ins.tick_params(labelsize=6)

fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)            # build_figures.py reads this
