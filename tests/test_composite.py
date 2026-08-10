import pandas as pd
import pytest

from elnino_readiness.index.composite import compute_index, priority_tier, quadrant


def test_gap_and_sort():
    df = pd.DataFrame({"area_name": ["A", "B"], "exposure": [90, 50], "readiness": [45, 55]})
    out = compute_index(df)
    assert list(out["gap"]) == [45, -5]
    assert out.iloc[0]["area_name"] == "A"


def test_tiers():
    assert priority_tier(45) == "critical"
    assert priority_tier(30) == "high"
    assert priority_tier(15) == "moderate"
    assert priority_tier(2) == "watch"


def test_quadrant():
    assert quadrant(90, 45) == "act first"
    assert quadrant(48, 66) == "lower priority"


def test_missing_columns():
    with pytest.raises(ValueError):
        compute_index(pd.DataFrame({"exposure": [1]}))
