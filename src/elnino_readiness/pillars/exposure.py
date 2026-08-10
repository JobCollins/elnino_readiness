"""Exposure pillar — the El Niño hazard footprint.

Converts CHIRPS rainfall anomaly (percentage of normal) into a 0–100
exposure score.  In the Greater Horn, El Niño drives **drought** (rainfall
deficit), so lower-than-normal rainfall → higher exposure.

When real anomaly data is not yet available (seed / illustrative runs),
the scorer falls back to a pass-through of the ``exposure`` column.
"""

from __future__ import annotations

import pandas as pd


def anomaly_to_exposure(pct_of_normal: pd.Series) -> pd.Series:
    """Convert percentage-of-normal rainfall to a 0–100 exposure score.

    Mapping (linear):
        ≤ 40 %  →  100  (extreme deficit — strong El Niño signal)
        100 %   →    0  (normal rainfall — no anomaly)
        > 100 % →    0  (surplus — not El Niño exposure for the Horn)

    Values between 40 % and 100 % are linearly interpolated.
    """
    score = (100.0 - pct_of_normal) / 60.0 * 100.0
    return score.clip(lower=0.0, upper=100.0)


def exposure_score(df: pd.DataFrame, col: str = "exposure") -> pd.Series:
    """0–100 exposure per area.

    If the DataFrame contains a ``rainfall_anomaly_pct`` column (produced by
    the zonal-stats pipeline), convert it via :func:`anomaly_to_exposure`.
    Otherwise fall back to the raw ``exposure`` column (seed data).
    """
    if "rainfall_anomaly_pct" in df.columns:
        return anomaly_to_exposure(df["rainfall_anomaly_pct"])
    return df[col].astype(float)
