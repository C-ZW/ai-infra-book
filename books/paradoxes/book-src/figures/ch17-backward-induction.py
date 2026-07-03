"""ch17: Backward induction chain for the unexpected hanging paradox.

Five weekday boxes (Mon..Fri). Arrows trace the prisoner's elimination
order running backward from Friday to Monday: eliminate Friday first
(base case), then reuse that conclusion to eliminate Thursday, and so
on down to Monday. Friday's elimination is boxed in a solid outline
(the one step nobody disputes); Thu..Mon are drawn with a dashed
outline and shaded band, marking where different schools of thought
(Quine 1953, Chow 1998, the "logical school") locate the disputed
reuse of the announcement. A star marks the day the hanging actually
happens (Wednesday) -- a genuine surprise despite the "proof" that no
day could work. Labels are English-only (Agg has no bundled CJK font);
the Chinese narration lives in the chapter text around this image.

Output: figures/out/ch17-backward-induction.svg
"""
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

OUT = Path(__file__).resolve().parent / "out" / "ch17-backward-induction.svg"
OUT.parent.mkdir(parents=True, exist_ok=True)

days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
order = [5, 4, 3, 2, 1]  # elimination order: Fri eliminated 1st, Mon last
w, h, y0, gap = 1.55, 1.15, 2.0, 0.55
xs = [0.6 + i * (w + gap) for i in range(5)]

fig, ax = plt.subplots(figsize=(10.6, 5.0))
ax.set_xlim(0, xs[-1] + w + 0.6)
ax.set_ylim(0, 5.0)
ax.axis("off")

# shaded band over Thu..Mon = the disputed reuse of the announcement
band = Rectangle((xs[0] - 0.3, y0 - 0.35), xs[3] + w - xs[0] + 0.6, h + 0.7,
                  facecolor="#f0dbb0", edgecolor="none", zorder=0, alpha=0.55)
ax.add_patch(band)
ax.text((xs[0] + xs[3] + w) / 2, y0 + h + 0.55,
        "disputed: each step re-uses the same announcement\none step earlier showed could fail",
        ha="center", fontsize=8.8, color="#7a4a12", style="italic")

for x, day, rank in zip(xs, days, order):
    solid = day == "Fri"
    edge = "#1a3a6b" if solid else "#8a5a1f"
    box = FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0.06,rounding_size=0.10",
                          linewidth=2.2 if solid else 1.6,
                          linestyle="solid" if solid else "dashed",
                          edgecolor=edge, facecolor="#dbe4f0" if solid else "#fff6e6", zorder=2)
    ax.add_patch(box)
    ax.text(x + w / 2, y0 + h - 0.32, day, ha="center", fontsize=13, weight="bold", zorder=3)
    ax.text(x + w / 2, y0 + 0.28, f"eliminated #{rank}", ha="center", fontsize=8.3, zorder=3,
            color=edge)

# backward arrows: Fri -> Thu -> Wed -> Tue -> Mon
arrow_style = dict(arrowstyle="-|>", mutation_scale=18, color="0.3", linewidth=1.6,
                    connectionstyle="arc3,rad=-0.35")
for i in range(4, 0, -1):
    ax.add_patch(FancyArrowPatch((xs[i] + 0.1, y0 + h + 0.15), (xs[i - 1] + w - 0.1, y0 + h + 0.15),
                                  **arrow_style))
ax.text(xs[0] - 0.05, y0 - 0.75, "base case: rule out Fri\n(the one solid step)",
        ha="left", fontsize=8.8, color="#1a3a6b")

# star: the actual hanging, Wednesday
sx = xs[2] + w / 2
ax.plot(sx, y0 - 0.85, marker="*", markersize=22, color="#a4161a", zorder=4)
ax.text(sx, y0 - 1.25, "the hanging actually happens here --\ngenuine surprise, despite the \"proof\"",
        ha="center", fontsize=9, color="#a4161a")

ax.set_title("Backward induction: the elimination chain and where it is disputed", fontsize=12.5, pad=14)
fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print("wrote", OUT)
