"""Population-weighted zonal statistics for raster-to-admin aggregation.

Given a values raster (e.g. CHIRPS rainfall anomaly) and an optional
population-weights raster (WorldPop), compute the (weighted) mean value
within each admin polygon. Uses windowed reads to avoid loading full
continental rasters into memory.
"""

from __future__ import annotations

import logging
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import Window, from_bounds

logger = logging.getLogger(__name__)


def _read_window(
    src: rasterio.DatasetReader, geom_bounds: tuple
) -> tuple[np.ndarray, rasterio.Affine, float | None]:
    """Read the raster window covering *geom_bounds*, return (data, transform, nodata)."""
    minx, miny, maxx, maxy = geom_bounds
    window = from_bounds(minx, miny, maxx, maxy, src.transform)
    # Clamp to valid raster extent
    try:
        window = window.intersection(Window(0, 0, src.width, src.height))
    except rasterio.errors.WindowError:
        return np.array([]), src.transform, src.nodata
    if window.width < 1 or window.height < 1:
        return np.array([]), src.transform, src.nodata
    data = src.read(1, window=window).astype(np.float64)
    transform = src.window_transform(window)
    return data, transform, src.nodata


def _mask_polygon(shape, data: np.ndarray, transform: rasterio.Affine) -> np.ndarray:
    """Return a boolean mask (True = outside polygon) for *data* grid."""
    if data.size == 0:
        return np.ones_like(data, dtype=bool)
    mask = geometry_mask(
        [shape],
        out_shape=data.shape,
        transform=transform,
        invert=False,  # True = outside
    )
    return mask


_NODATA_SENTINEL = -9999.0


def _weighted_mean(
    values: np.ndarray,
    mask: np.ndarray,
    weights: np.ndarray | None,
    values_nodata: float | None,
    weights_nodata: float | None,
) -> float:
    """Compute (optionally weighted) mean of unmasked, valid pixels."""
    valid = ~mask
    if values_nodata is not None:
        valid &= values != values_nodata
    # Always exclude the common -9999 sentinel even if nodata is None
    valid &= values > _NODATA_SENTINEL
    if weights is not None and weights_nodata is not None:
        valid &= weights != weights_nodata
    if weights is not None:
        valid &= weights > 0

    if not valid.any():
        return float("nan")

    v = values[valid]
    if weights is not None:
        w = weights[valid]
        return float(np.average(v, weights=w))
    return float(np.mean(v))


def zonal_stats(
    gdf: gpd.GeoDataFrame,
    values_path: Path,
    weights_path: Path | None = None,
) -> pd.Series:
    """Compute per-polygon (population-weighted) mean of a values raster.

    Parameters
    ----------
    gdf : GeoDataFrame
        Must contain a ``geometry`` column with polygons.
    values_path : Path
        Single-band GeoTIFF with the values to aggregate (e.g. anomaly).
    weights_path : Path | None
        Optional single-band GeoTIFF with population weights.

    Returns
    -------
    pd.Series
        One value per row of *gdf*, indexed the same way.
    """
    results: list[float] = []
    with rasterio.open(values_path) as val_src:
        wgt_src = rasterio.open(weights_path) if weights_path else None
        try:
            for geom in gdf.geometry:
                bounds = geom.bounds  # (minx, miny, maxx, maxy)
                v_data, v_tf, v_nd = _read_window(val_src, bounds)
                if v_data.size == 0:
                    results.append(float("nan"))
                    continue
                poly_mask = _mask_polygon(geom, v_data, v_tf)

                w_data: np.ndarray | None = None
                w_nd: float | None = None
                if wgt_src is not None:
                    w_data, w_tf, w_nd = _read_window(wgt_src, bounds)
                    # Resample weights to match values grid if shapes differ
                    if w_data.size > 0 and w_data.shape != v_data.shape:
                        w_data = _resample_to_shape(wgt_src, bounds, v_data.shape)

                results.append(_weighted_mean(v_data, poly_mask, w_data, v_nd, w_nd))
        finally:
            if wgt_src is not None:
                wgt_src.close()

    return pd.Series(results, index=gdf.index, name="zonal_mean")


def _resample_to_shape(
    src: rasterio.DatasetReader,
    bounds: tuple,
    target_shape: tuple[int, int],
) -> np.ndarray:
    """Read a window from *src* and resample it to *target_shape*."""
    from rasterio.enums import Resampling

    minx, miny, maxx, maxy = bounds
    window = from_bounds(minx, miny, maxx, maxy, src.transform)
    window = window.intersection(Window(0, 0, src.width, src.height))
    out = np.empty(target_shape, dtype=np.float64)
    src.read(1, window=window, out=out, resampling=Resampling.bilinear)
    return out
