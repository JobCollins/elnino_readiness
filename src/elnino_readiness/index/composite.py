"""Composite index: combine pillars into the readiness-vs-exposure headline.

The headline metric is the *gap* = exposure - readiness. A high positive gap
means high exposure with low readiness: the "act first" group. See the concept
note in docs/ for the full framing.
"""

from __future__ import annotations

import pandas as pd

EXPOSURE = "exposure"
READINESS = "readiness"
GAP = "gap"


def normalize(s: pd.Series) -> pd.Series:
    """Min-max scale a series to 0-100 (returns 50 for a constant series)."""
    lo, hi = s.min(), s.max()
    if hi == lo:
        return pd.Series(50.0, index=s.index)
    return (s - lo) / (hi - lo) * 100.0


def priority_tier(gap: float) -> str:
    if gap >= 40:
        return "critical"
    if gap >= 25:
        return "high"
    if gap >= 10:
        return "moderate"
    return "watch"


def quadrant(exposure: float, readiness: float, exp_high: float = 60, rdy_low: float = 50) -> str:
    hi_exp = exposure >= exp_high
    lo_rdy = readiness < rdy_low
    if hi_exp and lo_rdy:
        return "act first"
    if hi_exp:
        return "exposed but ready"
    if lo_rdy:
        return "low exposure, low readiness"
    return "lower priority"


def compute_index(df: pd.DataFrame) -> pd.DataFrame:
    """Add gap, priority_tier and quadrant; sort by gap descending."""
    missing = {EXPOSURE, READINESS} - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    out = df.copy()
    out[GAP] = out[EXPOSURE] - out[READINESS]
    out["priority_tier"] = out[GAP].apply(priority_tier)
    out["quadrant"] = out.apply(lambda r: quadrant(r[EXPOSURE], r[READINESS]), axis=1)
    return out.sort_values(GAP, ascending=False).reset_index(drop=True)
