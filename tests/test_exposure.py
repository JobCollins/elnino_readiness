"""Tests for the exposure pillar scoring."""

from __future__ import annotations

import pandas as pd
import pytest

from elnino_readiness.pillars.exposure import anomaly_to_exposure, exposure_score


class TestAnomalyToExposure:
    def test_normal_rainfall_zero_exposure(self):
        s = pd.Series([100.0])
        assert anomaly_to_exposure(s).iloc[0] == pytest.approx(0.0)

    def test_extreme_deficit_full_exposure(self):
        s = pd.Series([40.0])
        assert anomaly_to_exposure(s).iloc[0] == pytest.approx(100.0)

    def test_moderate_deficit(self):
        # 70% of normal → (100 - 70) / 60 * 100 = 50
        s = pd.Series([70.0])
        assert anomaly_to_exposure(s).iloc[0] == pytest.approx(50.0)

    def test_surplus_clamped_to_zero(self):
        s = pd.Series([120.0])
        assert anomaly_to_exposure(s).iloc[0] == pytest.approx(0.0)

    def test_below_40_clamped_to_100(self):
        s = pd.Series([0.0, 20.0])
        result = anomaly_to_exposure(s)
        assert (result == 100.0).all()

    def test_vectorised(self):
        s = pd.Series([40.0, 70.0, 100.0, 130.0])
        result = anomaly_to_exposure(s)
        expected = [100.0, 50.0, 0.0, 0.0]
        for got, want in zip(result, expected, strict=True):
            assert got == pytest.approx(want)


class TestExposureScore:
    def test_seed_passthrough(self):
        df = pd.DataFrame({"exposure": [82.0, 55.0]})
        result = exposure_score(df)
        assert list(result) == [82.0, 55.0]

    def test_live_anomaly_column(self):
        df = pd.DataFrame({"rainfall_anomaly_pct": [70.0], "exposure": [999.0]})
        result = exposure_score(df)
        # Should use rainfall_anomaly_pct, not the raw exposure column
        assert result.iloc[0] == pytest.approx(50.0)
