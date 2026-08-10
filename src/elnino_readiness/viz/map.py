"""Visual outputs for the readiness index."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def plot_quadrant(
    df: pd.DataFrame, out_path: str | Path, exp_high: float = 60, rdy_low: float = 50
) -> Path:
    """Scatter of exposure vs readiness, shading the 'act first' quadrant."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.set_xlim(20, 80)
    ax.set_ylim(40, 100)
    ax.add_patch(
        Rectangle(
            (20, exp_high), rdy_low - 20, 100 - exp_high, color="#E24B4A", alpha=0.10, zorder=0
        )
    )
    ax.axhline(exp_high, color="#999", lw=0.8, ls="--", zorder=1)
    ax.axvline(rdy_low, color="#999", lw=0.8, ls="--", zorder=1)

    danger = (df["exposure"] >= exp_high) & (df["readiness"] < rdy_low)
    colors = danger.map({True: "#E24B4A", False: "#378ADD"})
    ax.scatter(
        df["readiness"], df["exposure"], c=colors, s=70, edgecolor="white", linewidth=1.2, zorder=3
    )
    for _, r in df.iterrows():
        ax.annotate(
            r.get("area_name", r.get("area_id", "")),
            (r["readiness"], r["exposure"]),
            xytext=(5, 4),
            textcoords="offset points",
            fontsize=8,
        )

    ax.set_xlabel("Readiness →")
    ax.set_ylabel("Exposure →")
    ax.set_title("Exposure vs readiness (top-left = act first)")
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_choropleth(df: pd.DataFrame, boundaries_path, out_path):
    """TODO(Phase 0): admin-level choropleth of the gap.

    Requires the `geo` extras (geopandas) and an admin-boundary file joined on
    area_id. Colour by `gap` with a diverging ramp (red = high gap).
    """
    raise NotImplementedError(
        "Install geo extras (pip install -e '.[geo]') and provide an admin "
        "boundary file to render the choropleth."
    )
