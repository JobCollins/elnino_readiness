"""Tests for WorldPop population ingest."""

from __future__ import annotations

import pytest

from elnino_readiness.ingest.worldpop import _country_url


class TestURLConstruction:
    def test_url_format_kenya(self):
        url = _country_url("KEN")
        assert "KEN" in url
        assert "ken_ppp_2020" in url
        assert url.endswith(".tif")

    def test_url_format_case_insensitive(self):
        assert _country_url("ken") == _country_url("KEN")


@pytest.mark.network
def test_download_djibouti(tmp_path):
    """Download Djibouti population raster (smallest country, ~100KB)."""
    import rasterio

    from elnino_readiness.ingest.worldpop import download_population

    path = download_population("DJI", cache_dir=tmp_path)
    assert path.exists()
    with rasterio.open(path) as src:
        assert src.count == 1
        assert src.width > 0
        assert src.crs is not None
