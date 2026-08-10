"""Readiness pillar — the differentiator. Is preparedness actually in place?

This layer is mostly hand-compiled per admin unit and must be documented and
sourced. Keep the sub-indicators explicit so the score is auditable.

TODO(Phase 0): score each sub-indicator per area from CERF/DREF anticipatory
financing, the IGAD/ICPAC trigger matrices, national contingency plans, WFP
prepositioning, and a last-mile check. Weight and combine to 0-100.
"""

from __future__ import annotations

import pandas as pd

READINESS_SUBINDICATORS = {
    "anticipatory_finance": "Pre-agreed CERF/DREF triggers in place",
    "contingency_plan": "Current national/sub-national plan exists and is tested",
    "prepositioning": "Relief stocks prepositioned within reach",
    "last_mile": "Trained local response team + functioning transfer channel",
}


def readiness_score(df: pd.DataFrame, col: str = "readiness") -> pd.Series:
    """0-100 readiness per area. Placeholder: passes through seed `readiness`."""
    return df[col].astype(float)
