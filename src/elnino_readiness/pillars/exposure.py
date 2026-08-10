"""Exposure pillar — the El Niño hazard footprint.

TODO(Phase 0): build from ingest.chirps (rainfall anomaly / SPI), ingest.enso
(seasonal signal) and NDVI/VHI vegetation stress, bias-corrected, downscaled and
population-weighted to the target admin level. See docs/ concept note section 3
and the data-source matrix.
"""

from __future__ import annotations

import pandas as pd


def exposure_score(df: pd.DataFrame, col: str = "exposure") -> pd.Series:
    """0-100 exposure per area. Placeholder: passes through seed `exposure`."""
    return df[col].astype(float)
