"""WorldPop gridded population ingest (exposure weighting).

Downloads country-level 1 km population rasters from WorldPop and
optionally merges them into a single regional mosaic for use as
population weights in zonal aggregation.
"""

from __future__ import annotations

import logging
from pathlib import Path

import rasterio
import requests
from rasterio.merge import merge

logger = logging.getLogger(__name__)

SOURCE = {
    "name": "WorldPop",
    "provider": "University of Southampton",
    "url": "https://www.worldpop.org",
    "resolution": "~1km (0.00833deg)",
    "year": 2020,
    "license": "CC-BY 4.0",
}

WORLDPOP_URL = (
    "https://data.worldpop.org/GIS/Population/"
    "Global_2000_2020_1km_UNadj/2020/{ISO3}/"
    "{iso3_lower}_ppp_2020_1km_Aggregated_UNadj.tif"
)


def _country_url(iso3: str) -> str:
    return WORLDPOP_URL.format(ISO3=iso3.upper(), iso3_lower=iso3.lower())


def download_population(
    iso3: str,
    cache_dir: Path = Path("data/raw/worldpop"),
) -> Path:
    """Download the 1 km population raster for one country.  Cache locally."""
    iso3 = iso3.upper()
    dest = cache_dir / f"{iso3}_pop_2020_1km.tif"
    if dest.exists():
        logger.info("Cached: %s", dest)
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = _country_url(iso3)
    logger.info("Downloading WorldPop %s → %s", iso3, dest)
    resp = requests.get(url, timeout=120, stream=True)
    resp.raise_for_status()
    with open(dest, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=1 << 16):
            fh.write(chunk)
    return dest


def merge_population(
    iso3_list: list[str],
    cache_dir: Path = Path("data/raw/worldpop"),
    out_dir: Path = Path("data/interim/worldpop"),
) -> Path:
    """Download and merge population rasters for *iso3_list* into one mosaic.

    Returns the path to the merged GeoTIFF.
    """
    out_path = out_dir / "pop_mosaic.tif"
    if out_path.exists():
        logger.info("Cached mosaic: %s", out_path)
        return out_path

    paths = [download_population(iso3, cache_dir=cache_dir) for iso3 in iso3_list]
    datasets = [rasterio.open(p) for p in paths]
    try:
        mosaic, transform = merge(datasets)
    finally:
        for ds in datasets:
            ds.close()

    out_dir.mkdir(parents=True, exist_ok=True)
    profile = datasets[0].profile.copy()
    profile.update(
        driver="GTiff",
        height=mosaic.shape[1],
        width=mosaic.shape[2],
        transform=transform,
        count=1,
        dtype=mosaic.dtype,
        compress="lzw",
    )
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(mosaic[0], 1)

    logger.info("Merged population mosaic: %s (%d countries)", out_path, len(iso3_list))
    return out_path
