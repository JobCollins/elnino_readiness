"""Admin boundary loader for IGAD priority countries.

Downloads admin-1 and admin-2 geometries from the geoBoundaries API, caches
them locally, and returns GeoDataFrames with a canonical column schema so
every downstream layer can join on ``area_id``.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

import geopandas as gpd
import requests
import yaml

logger = logging.getLogger(__name__)

SOURCE = {
    "name": "geoBoundaries",
    "provider": "William & Mary geoLab",
    "url": "https://www.geoboundaries.org",
    "license": "CC-BY 4.0 (gbOpen)",
    "api": "https://www.geoboundaries.org/api/current/gbOpen/{iso3}/ADM{level}/",
}

# Canonical column contract — every boundaries GeoDataFrame has exactly these.
CANONICAL_COLUMNS = ["area_id", "area_name", "country_iso3", "admin_level", "geometry"]

_API_URL = SOURCE["api"]


def _cache_path(cache_dir: Path, iso3: str, admin_level: int) -> Path:
    return cache_dir / f"{iso3}_ADM{admin_level}.geojson"


def fetch_admin_boundaries(
    iso3: str,
    admin_level: int,
    cache_dir: Path = Path("data/raw/boundaries"),
) -> gpd.GeoDataFrame:
    """Fetch admin boundaries for one country at the given level.

    Downloads from the geoBoundaries open API on first call, then reads from
    a local GeoJSON cache on subsequent calls.

    Returns a GeoDataFrame with the canonical columns (see ``CANONICAL_COLUMNS``).
    """
    if admin_level not in (1, 2):
        raise ValueError(f"admin_level must be 1 or 2, got {admin_level}")

    iso3 = iso3.upper()
    cached = _cache_path(cache_dir, iso3, admin_level)

    if cached.exists():
        logger.info("Loading cached boundaries: %s", cached)
        gdf = gpd.read_file(cached)
    else:
        url = _API_URL.format(iso3=iso3, level=admin_level)
        logger.info("Fetching geoBoundaries metadata: %s", url)
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        meta = resp.json()

        gjson_url = meta["gjDownloadURL"]
        logger.info("Downloading GeoJSON: %s", gjson_url)
        gjson_resp = requests.get(gjson_url, timeout=120)
        gjson_resp.raise_for_status()

        cache_dir.mkdir(parents=True, exist_ok=True)
        cached.write_text(gjson_resp.text, encoding="utf-8")
        gdf = gpd.read_file(cached)

    return _standardise(gdf, iso3, admin_level)


def _standardise(gdf: gpd.GeoDataFrame, iso3: str, admin_level: int) -> gpd.GeoDataFrame:
    """Map raw geoBoundaries columns to the canonical schema."""
    # geoBoundaries uses shapeID (globally unique) and shapeName.
    out = gpd.GeoDataFrame(
        {
            "area_id": gdf["shapeID"],
            "area_name": gdf["shapeName"],
            "country_iso3": iso3,
            "admin_level": admin_level,
            "geometry": gdf["geometry"],
        },
        crs=gdf.crs,
    )
    return out.reset_index(drop=True)


def standardise_dataframe(
    gdf: gpd.GeoDataFrame,
    iso3: str,
    admin_level: int,
    id_col: str = "shapeID",
    name_col: str = "shapeName",
) -> gpd.GeoDataFrame:
    """Public helper: standardise any GeoDataFrame to canonical columns.

    Useful for unit tests that build synthetic frames without hitting the API.
    """
    out = gpd.GeoDataFrame(
        {
            "area_id": gdf[id_col],
            "area_name": gdf[name_col],
            "country_iso3": iso3,
            "admin_level": admin_level,
            "geometry": gdf["geometry"],
        },
        crs=gdf.crs if gdf.crs else "EPSG:4326",
    )
    return out.reset_index(drop=True)


def load_priority_boundaries(
    admin_level: int,
    config_path: Path = Path("config/priority_areas.yaml"),
    cache_dir: Path = Path("data/raw/boundaries"),
    iso3_list: Iterable[str] | None = None,
) -> gpd.GeoDataFrame:
    """Load and concatenate boundaries for all priority countries.

    Parameters
    ----------
    admin_level : int
        1 or 2.
    config_path : Path
        Path to priority_areas.yaml (used when *iso3_list* is ``None``).
    cache_dir : Path
        Where to cache downloaded GeoJSON files.
    iso3_list : list[str] | None
        Override the config file with an explicit list of ISO-3 codes.
    """
    if iso3_list is None:
        with open(config_path, encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh)
        iso3_list = [c["iso3"] for c in cfg["countries"]]

    frames: list[gpd.GeoDataFrame] = []
    for iso3 in iso3_list:
        logger.info("Loading %s ADM%d …", iso3, admin_level)
        gdf = fetch_admin_boundaries(iso3, admin_level, cache_dir=cache_dir)
        frames.append(gdf)

    combined = gpd.GeoDataFrame(
        data=gpd.pd.concat(frames, ignore_index=True),
        crs=frames[0].crs if frames else "EPSG:4326",
    )
    dupes = combined["area_id"].duplicated()
    if dupes.any():
        raise ValueError(
            f"Duplicate area_id values after concatenation: "
            f"{combined.loc[dupes, 'area_id'].tolist()}"
        )
    return combined
