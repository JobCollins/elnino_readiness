"""CHIRPS rainfall anomaly ingest (exposure pillar).

Downloads Africa-wide monthly CHIRPS rainfall rasters and computes
**percentage of normal** by dividing observed rainfall by a multi-year
climatology for the same calendar month.  The result is written as a
GeoTIFF to ``data/interim/chirps/`` with nodata = -9999.

All raw downloads are cached under ``data/raw/chirps/``.
"""

from __future__ import annotations

import gzip
import logging
import shutil
from pathlib import Path

import numpy as np
import rasterio
import requests

logger = logging.getLogger(__name__)

SOURCE = {
    "name": "CHIRPS",
    "provider": "UCSB Climate Hazards Center",
    "url": "https://www.chc.ucsb.edu/data/chirps",
    "resolution": "0.05deg (~5km)",
    "cadence": "pentad/monthly",
}

# Full-Africa monthly (gzipped GeoTIFF) — covers all IGAD countries.
AFRICA_MONTHLY_URL = (
    "https://data.chc.ucsb.edu/products/CHIRPS-2.0"
    "/africa_monthly/tifs/chirps-v2.0.{year}.{month:02d}.tif.gz"
)

# Years used to build the per-pixel climatology mean.
CLIMATOLOGY_YEARS = range(2003, 2023)  # 20 years, good balance of coverage vs download

NODATA = -9999.0


def _download(url: str, dest: Path, *, gzipped: bool = False) -> Path:
    """Download *url* to *dest*, creating parent dirs.  Skip if cached."""
    if dest.exists():
        logger.info("Cached: %s", dest)
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading %s → %s", url, dest)
    resp = requests.get(url, timeout=180, stream=True)
    resp.raise_for_status()
    if gzipped:
        tmp = dest.with_suffix(dest.suffix + ".gz")
        with open(tmp, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                fh.write(chunk)
        with gzip.open(tmp, "rb") as gz, open(dest, "wb") as out:
            shutil.copyfileobj(gz, out)
        tmp.unlink()
    else:
        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                fh.write(chunk)
    return dest


def download_africa_monthly(
    year: int,
    month: int,
    cache_dir: Path = Path("data/raw/chirps"),
) -> Path:
    """Download the full-Africa monthly CHIRPS raster (gzipped GeoTIFF)."""
    url = AFRICA_MONTHLY_URL.format(year=year, month=month)
    return _download(url, cache_dir / f"chirps-v2.0.{year}.{month:02d}.tif", gzipped=True)


def build_climatology(
    month: int,
    cache_dir: Path = Path("data/raw/chirps"),
    out_dir: Path = Path("data/interim/chirps"),
    years: range = CLIMATOLOGY_YEARS,
) -> Path:
    """Build a pixel-wise mean rainfall for *month* across *years*.

    Downloads each year's raster if not cached, computes the mean
    (ignoring nodata), and writes to ``out_dir/climatology_{month:02d}.tif``.
    """
    out_path = out_dir / f"climatology_{month:02d}.tif"
    if out_path.exists():
        logger.info("Cached climatology: %s", out_path)
        return out_path

    logger.info("Building climatology for month %02d from %d years …", month, len(years))
    paths = []
    for yr in years:
        paths.append(download_africa_monthly(yr, month, cache_dir=cache_dir))

    # Read first raster for profile
    with rasterio.open(paths[0]) as ref:
        profile = ref.profile.copy()
        shape = (ref.height, ref.width)
        ref_nodata = ref.nodata

    # Accumulate sum and count (ignoring nodata)
    total = np.zeros(shape, dtype=np.float64)
    count = np.zeros(shape, dtype=np.int32)
    for p in paths:
        with rasterio.open(p) as src:
            data = src.read(1).astype(np.float64)
            valid = np.ones(shape, dtype=bool)
            if ref_nodata is not None:
                valid &= data != ref_nodata
            valid &= data > -9000  # sentinel guard
            total[valid] += data[valid]
            count[valid] += 1

    clim = np.full(shape, NODATA, dtype=np.float32)
    good = count > 0
    clim[good] = (total[good] / count[good]).astype(np.float32)

    out_dir.mkdir(parents=True, exist_ok=True)
    profile.update(dtype="float32", nodata=NODATA, compress="lzw")
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(clim, 1)

    logger.info(
        "Wrote climatology: %s (%d years, %d valid pixels)",
        out_path,
        len(years),
        good.sum(),
    )
    return out_path


def percentage_of_normal(
    observed: np.ndarray,
    climatology: np.ndarray,
    nodata: float = NODATA,
) -> np.ndarray:
    """Compute ``(observed / climatology) * 100``.

    Returns NODATA where climatology is zero/nodata or observed is nodata.
    """
    result = np.full_like(observed, nodata, dtype=np.float32)
    valid = (
        (observed != nodata)
        & (observed > -9000)
        & (climatology != nodata)
        & (climatology > -9000)
        & (climatology > 0)
    )
    result[valid] = (observed[valid] / climatology[valid] * 100.0).astype(np.float32)
    return result


def load_rainfall_anomaly(
    year: int,
    month: int,
    cache_dir: Path = Path("data/raw/chirps"),
    out_dir: Path = Path("data/interim/chirps"),
) -> Path:
    """Main entry point: return path to a percentage-of-normal anomaly raster.

    Downloads the observed Africa monthly raster for *year*/*month*, builds
    a climatology if needed, computes ``(observed / clim) * 100``, and writes
    the result to *out_dir*.  Values: 100 = normal, <100 = deficit, >100 = surplus.
    Nodata = -9999.
    """
    pct_path = out_dir / f"pct_normal.{year}.{month:02d}.tif"
    if pct_path.exists():
        logger.info("Cached pct-of-normal: %s", pct_path)
        return pct_path

    obs_path = download_africa_monthly(year, month, cache_dir=cache_dir)
    clim_path = build_climatology(month, cache_dir=cache_dir, out_dir=out_dir)

    with rasterio.open(obs_path) as obs_src, rasterio.open(clim_path) as clim_src:
        obs = obs_src.read(1).astype(np.float64)
        clim = clim_src.read(1).astype(np.float64)
        profile = obs_src.profile.copy()

    pct = percentage_of_normal(obs, clim)

    out_dir.mkdir(parents=True, exist_ok=True)
    profile.update(dtype="float32", nodata=NODATA, compress="lzw")
    with rasterio.open(pct_path, "w", **profile) as dst:
        dst.write(pct, 1)

    valid = pct[pct != NODATA]
    logger.info(
        "Wrote pct-of-normal: %s (valid px: %d, range: %.0f–%.0f%%)",
        pct_path,
        valid.size,
        np.min(valid),
        np.max(valid),
    )
    return pct_path
