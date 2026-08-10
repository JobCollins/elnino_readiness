"""Tests for CHIRPS rainfall anomaly ingest."""

from __future__ import annotations

import numpy as np
import pytest

from elnino_readiness.ingest.chirps import (
    AFRICA_MONTHLY_URL,
    NODATA,
    percentage_of_normal,
)


class TestURLConstruction:
    def test_africa_monthly_url(self):
        url = AFRICA_MONTHLY_URL.format(year=2026, month=6)
        assert url.endswith("/chirps-v2.0.2026.06.tif.gz")

    def test_month_zero_padded(self):
        url = AFRICA_MONTHLY_URL.format(year=2026, month=3)
        assert "chirps-v2.0.2026.03.tif.gz" in url


class TestPercentageOfNormal:
    def test_basic(self):
        obs = np.array([200.0, 50.0, 100.0])
        clim = np.array([100.0, 100.0, 100.0])
        result = percentage_of_normal(obs, clim)
        np.testing.assert_allclose(result, [200.0, 50.0, 100.0], rtol=1e-5)

    def test_zero_climatology_returns_nodata(self):
        obs = np.array([50.0, 0.0])
        clim = np.array([0.0, 0.0])
        result = percentage_of_normal(obs, clim)
        assert (result == NODATA).all()

    def test_nodata_input_propagates(self):
        obs = np.array([NODATA, 80.0])
        clim = np.array([100.0, 100.0])
        result = percentage_of_normal(obs, clim)
        assert result[0] == NODATA
        np.testing.assert_allclose(result[1], 80.0, rtol=1e-5)

    def test_shape_preserved(self):
        obs = np.ones((3, 4)) * 80.0
        clim = np.ones((3, 4)) * 100.0
        result = percentage_of_normal(obs, clim)
        assert result.shape == (3, 4)


@pytest.mark.network
def test_download_africa_monthly(tmp_path):
    """Download one Africa monthly raster and verify it's a valid GeoTIFF."""
    import rasterio

    from elnino_readiness.ingest.chirps import download_africa_monthly

    path = download_africa_monthly(2023, 1, cache_dir=tmp_path)
    assert path.exists()
    assert path.suffix == ".tif"
    with rasterio.open(path) as src:
        assert src.count == 1
        assert src.width > 0
        assert src.height > 0
        assert src.crs is not None
