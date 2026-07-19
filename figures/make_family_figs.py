"""Generate the cross-family figures for the manuscript.

Numbers are the small-/large-model lenient exact-match accuracies produced by
`src/score_family.py` (results/summary_family.md). Two figures:

  fig_lookup_equalizer   grouped bars: main-lookup accuracy (small-markdown,
                         small-verbalized, large-markdown) x 5 families.
  fig_verbalization_delta heatmap of the verbalization effect on the SMALL model
                         (verbalized - markdown, percentage points) across the
                         lookup task and the five stress structures.

Output: PDF (for LaTeX) + PNG (for the markdown/preview), in this directory.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#666666",
    "axes.linewidth": 0.8,
    "figure.dpi": 200,
})

FAMILIES = ["Llama 3\n(8B/70B)", "Qwen2.5\n(7B/72B)", "Qwen3.5\n(9B/27B)",
            "Mistral\n(12B/24B)", "Gemma 3\n(12B/27B)"]

# --- main lookup accuracy (%), from summary_family.md -------------------------
small_md   = [75, 93, 87, 88, 98]
small_verb = [100, 97, 88, 100, 100]
large_md   = [100, 100, 100, 95, 93]

# Okabe-Ito colourblind-safe trio
C_SMD, C_SVB, C_LMD = "#0072B2", "#E69F00", "#009E73"


def fig_lookup(path_stem: str) -> None:
    x = np.arange(len(FAMILIES))
    w = 0.26
    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    b1 = ax.bar(x - w, small_md, w, label="small · markdown", color=C_SMD)
    b2 = ax.bar(x, small_verb, w, label="small · verbalized", color=C_SVB)
    b3 = ax.bar(x + w, large_md, w, label="large · markdown", color=C_LMD)
    for bars in (b1, b2, b3):
        for r in bars:
            ax.annotate(f"{int(r.get_height())}", (r.get_x() + r.get_width() / 2,
                        r.get_height()), textcoords="offset points",
                        xytext=(0, 2), ha="center", fontsize=7, color="#333333")
    ax.set_ylabel("Cell-lookup exact match (%)")
    ax.set_ylim(0, 108)
    ax.set_xticks(x)
    ax.set_xticklabels(FAMILIES)
    ax.set_yticks(range(0, 101, 25))
    ax.axhline(100, color="#cccccc", lw=0.6, zorder=0)
    ax.legend(frameon=False, ncol=3, loc="lower center",
              bbox_to_anchor=(0.5, -0.32), fontsize=8)
    ax.set_title("Table verbalization equalizes scale only where the small model "
                 "reads markdown poorly", fontsize=8.5, loc="left", pad=6)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(f"{path_stem}.{ext}", bbox_inches="tight")
    plt.close(fig)


# --- verbalization delta (verb - md) on the SMALL model, percentage points ----
TASKS = ["Lookup", "Wide", "Multilevel", "Aggregation", "Arithmetic", "3-level\nheader"]
# rows = families (short), cols = TASKS
DELTA = np.array([
    [+25,  -2, -44,  -2, +16, -17],   # Llama 3 8B
    [ +4,  -4, -40, -15, +11, -31],   # Qwen2.5 7B
    [ +1,   0,  -8,   0,  -2, -81],   # Qwen3.5 9B
    [+12,  -2, -42,  -6,  +4, -27],   # Mistral 12B
    [ +2,  +2, -17,  +2,  +4, -37],   # Gemma 3 12B
], dtype=float)
FAM_SHORT = ["Llama 3 8B", "Qwen2.5 7B", "Qwen3.5 9B", "Mistral 12B", "Gemma 3 12B"]


# hybrid delta (hybrid - markdown) on the SMALL model, percentage points
HYBRID_DELTA = np.array([
    [+23,  0,   0,  +4, +4,  -2],   # Llama 3 8B
    [ +5, -4, -15,  -8, +17, -15],  # Qwen2.5 7B
    [+10,  0,   0,   0,  0,  -6],   # Qwen3.5 9B
    [+12,  0, -10,  -8, +4,  +2],   # Mistral 12B
    [ +2, +6,  +2, +10, +8,  +4],   # Gemma 3 12B
], dtype=float)


def fig_delta(path_stem: str) -> None:
    vmax = max(np.abs(DELTA).max(), np.abs(HYBRID_DELTA).max())
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.1), sharey=True)
    for ax, M, sub in zip(axes, [DELTA, HYBRID_DELTA],
                          ["Verbalized − markdown", "Hybrid − markdown"]):
        im = ax.imshow(M, cmap="RdBu", norm=norm, aspect="auto")
        ax.set_xticks(range(len(TASKS)))
        ax.set_xticklabels([t.replace("\n", " ") for t in TASKS], fontsize=7.5,
                           rotation=30, ha="right")
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                v = M[i, j]
                ax.text(j, i, f"{v:+.0f}", ha="center", va="center", fontsize=7,
                        color="white" if abs(v) > vmax * 0.55 else "#222222")
        ax.set_xticks(np.arange(-.5, len(TASKS), 1), minor=True)
        ax.set_yticks(np.arange(-.5, len(FAM_SHORT), 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=2)
        ax.tick_params(which="minor", length=0)
        ax.set_title(sub, fontsize=9)
    axes[0].set_yticks(range(len(FAM_SHORT)))
    axes[0].set_yticklabels(FAM_SHORT, fontsize=8)
    cbar = fig.colorbar(im, ax=axes, fraction=0.020, pad=0.02)
    cbar.set_label("Δ accuracy (pp)", fontsize=8)
    cbar.ax.tick_params(labelsize=7)
    fig.suptitle("Verbalization harms ambiguous headers (left); the hybrid "
                 "representation neutralizes the damage (right)", fontsize=9)
    for ext in ("pdf", "png"):
        fig.savefig(f"{path_stem}.{ext}", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    fig_lookup(os.path.join(here, "fig_lookup_equalizer"))
    fig_delta(os.path.join(here, "fig_verbalization_delta"))
    print("wrote fig_lookup_equalizer.{pdf,png} and fig_verbalization_delta.{pdf,png}")
