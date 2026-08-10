"""Tests for the admin boundary loader."""

from __future__ import annotations

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from elnino_readiness.ingest.boundaries import (
    CANONICAL_COLUMNS,
    standardise_dataframe,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _synthetic_gdf(n: int = 5, iso3: str = "KEN", admin_level: int = 1) -> gpd.GeoDataFrame:
    """Build a tiny synthetic GeoDataFrame mimicking geoBoundaries output."""
    raw = gpd.GeoDataFrame(
        {
            "shapeID": [f"{iso3}-ADM{admin_level}-{i}" for i in range(n)],
            "shapeName": [f"Region_{i}" for i in range(n)],
            "geometry": [box(i, 0, i + 1, 1) for i in range(n)],
        },
        crs="EPSG:4326",
    )
    return raw


# ---------------------------------------------------------------------------
# Unit tests (no network)
# ---------------------------------------------------------------------------


class TestStandardise:
    """Validate schema, uniqueness, and join logic using synthetic data."""

    def test_canonical_columns(self):
        raw = _synthetic_gdf()
        std = standardise_dataframe(raw, iso3="KEN", admin_level=1)
        assert list(std.columns) == CANONICAL_COLUMNS

    def test_area_id_unique(self):
        raw = _synthetic_gdf(n=10)
        std = standardise_dataframe(raw, iso3="KEN", admin_level=1)
        assert std["area_id"].is_unique

    def test_country_iso3_populated(self):
        raw = _synthetic_gdf(iso3="ETH")
        std = standardise_dataframe(raw, iso3="ETH", admin_level=2)
        assert (std["country_iso3"] == "ETH").all()
        assert (std["admin_level"] == 2).all()

    def test_crs_preserved(self):
        raw = _synthetic_gdf()
        std = standardise_dataframe(raw, iso3="KEN", admin_level=1)
        assert std.crs is not None
        assert std.crs.to_epsg() == 4326

    def test_join_with_pillar_data(self):
        """Simulate the canonical join: pillar scores keyed on area_id."""
        raw = _synthetic_gdf(n=4, iso3="SOM", admin_level=1)
        boundaries = standardise_dataframe(raw, iso3="SOM", admin_level=1)

        # Pillar data covering all boundary units
        pillar = pd.DataFrame(
            {
                "area_id": boundaries["area_id"].tolist(),
                "exposure": [80, 70, 60, 50],
                "readiness": [30, 55, 65, 40],
            }
        )

        merged = boundaries.merge(pillar, on="area_id", how="inner")

        # No orphans on either side
        assert len(merged) == len(boundaries)
        assert len(merged) == len(pillar)
        assert "exposure" in merged.columns
        assert "geometry" in merged.columns

    def test_join_detects_missing_areas(self):
        """Outer join surfaces areas with no pillar data."""
        raw = _synthetic_gdf(n=3, iso3="DJI", admin_level=1)
        boundaries = standardise_dataframe(raw, iso3="DJI", admin_level=1)

        # Pillar covers only the first unit
        pillar = pd.DataFrame(
            {
                "area_id": [boundaries["area_id"].iloc[0]],
                "exposure": [55],
            }
        )

        merged = boundaries.merge(pillar, on="area_id", how="left")
        missing = merged["exposure"].isna().sum()
        assert missing == 2  # two boundary units have no pillar data


# ---------------------------------------------------------------------------
# Integration test — hits geoBoundaries API (skip in CI)
# ---------------------------------------------------------------------------


@pytest.mark.network
def test_fetch_djibouti_adm1(tmp_path):
    """Fetch Djibouti ADM1 (smallest country) and validate schema."""
    from elnino_readiness.ingest.boundaries import fetch_admin_boundaries

    gdf = fetch_admin_boundaries("DJI", admin_level=1, cache_dir=tmp_path)

    assert list(gdf.columns) == CANONICAL_COLUMNS
    assert len(gdf) > 0
    assert gdf["area_id"].is_unique
    assert (gdf["country_iso3"] == "DJI").all()
    assert (gdf["admin_level"] == 1).all()
    assert gdf.crs is not None
