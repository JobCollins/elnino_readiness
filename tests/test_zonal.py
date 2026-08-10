"""Tests for population-weighted zonal statistics."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_bounds
from shapely.geometry import box

from elnino_readiness.ingest.zonal import zonal_stats


def _write_tif(path: Path, data: np.ndarray, bounds: tuple, nodata: float = -9999.0):
    """Write a small single-band GeoTIFF for testing."""
    h, w = data.shape
    transform = from_bounds(*bounds, w, h)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=h,
        width=w,
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=transform,
        nodata=nodata,
    ) as dst:
        dst.write(data, 1)


class TestZonalStats:
    """Unit tests using small synthetic rasters."""

    def test_unweighted_mean(self, tmp_path):
        """Polygon covering all pixels → simple mean."""
        data = np.array([[10.0, 20.0], [30.0, 40.0]])
        tif = tmp_path / "values.tif"
        bounds = (0, 0, 2, 2)
        _write_tif(tif, data, bounds)

        gdf = gpd.GeoDataFrame(geometry=[box(0, 0, 2, 2)], crs="EPSG:4326")
        result = zonal_stats(gdf, tif)

        assert len(result) == 1
        assert result.iloc[0] == pytest.approx(25.0)

    def test_weighted_mean(self, tmp_path):
        """Population-weighted mean gives more weight to populated pixels."""
        values = np.array([[10.0, 20.0], [30.0, 40.0]])
        # All population in top-left pixel
        weights = np.array([[100.0, 0.0], [0.0, 0.0]])
        bounds = (0, 0, 2, 2)
        _write_tif(tmp_path / "v.tif", values, bounds)
        _write_tif(tmp_path / "w.tif", weights, bounds)

        gdf = gpd.GeoDataFrame(geometry=[box(0, 0, 2, 2)], crs="EPSG:4326")
        result = zonal_stats(gdf, tmp_path / "v.tif", tmp_path / "w.tif")

        # Only the top-left pixel (value=10) has population
        assert result.iloc[0] == pytest.approx(10.0)

    def test_nodata_excluded(self, tmp_path):
        """Pixels with nodata are excluded from the mean."""
        data = np.array([[10.0, -9999.0], [30.0, 40.0]])
        tif = tmp_path / "values.tif"
        bounds = (0, 0, 2, 2)
        _write_tif(tif, data, bounds, nodata=-9999.0)

        gdf = gpd.GeoDataFrame(geometry=[box(0, 0, 2, 2)], crs="EPSG:4326")
        result = zonal_stats(gdf, tif)

        # Mean of 10, 30, 40 (nodata excluded)
        assert result.iloc[0] == pytest.approx(80.0 / 3)

    def test_polygon_outside_raster_returns_nan(self, tmp_path):
        """Polygon completely outside the raster extent → NaN."""
        data = np.array([[10.0, 20.0], [30.0, 40.0]])
        tif = tmp_path / "values.tif"
        _write_tif(tif, data, bounds=(0, 0, 2, 2))

        gdf = gpd.GeoDataFrame(geometry=[box(10, 10, 12, 12)], crs="EPSG:4326")
        result = zonal_stats(gdf, tif)

        assert np.isnan(result.iloc[0])

    def test_multiple_polygons(self, tmp_path):
        """Multiple polygons each get their own stat."""
        # 4x4 grid, values 0..15
        data = np.arange(16, dtype=np.float64).reshape(4, 4)
        tif = tmp_path / "values.tif"
        _write_tif(tif, data, bounds=(0, 0, 4, 4))

        gdf = gpd.GeoDataFrame(
            geometry=[box(0, 2, 2, 4), box(2, 0, 4, 2)],
            crs="EPSG:4326",
        )
        result = zonal_stats(gdf, tif)

        assert len(result) == 2
        # Both polygons should return finite values
        assert all(np.isfinite(result))

    def test_index_preserved(self, tmp_path):
        """Result Series has the same index as the input GeoDataFrame."""
        data = np.ones((2, 2))
        tif = tmp_path / "values.tif"
        _write_tif(tif, data, bounds=(0, 0, 2, 2))

        gdf = gpd.GeoDataFrame(
            {"area_id": ["A", "B"]},
            geometry=[box(0, 0, 1, 1), box(1, 1, 2, 2)],
            crs="EPSG:4326",
        )
        gdf = gdf.set_index("area_id")
        result = zonal_stats(gdf, tif)

        assert list(result.index) == ["A", "B"]

    def test_sentinel_nodata_excluded(self, tmp_path):
        """Pixels with -9999 sentinel are excluded even when nodata metadata is None."""
        data = np.array([[10.0, -9999.0], [30.0, 40.0]])
        tif = tmp_path / "values.tif"
        bounds = (0, 0, 2, 2)
        # Write with nodata=None (not declared in metadata)
        _write_tif(tif, data, bounds, nodata=None)

        gdf = gpd.GeoDataFrame(geometry=[box(0, 0, 2, 2)], crs="EPSG:4326")
        result = zonal_stats(gdf, tif)

        # Mean of 10, 30, 40 — sentinel excluded
        assert result.iloc[0] == pytest.approx(80.0 / 3)
