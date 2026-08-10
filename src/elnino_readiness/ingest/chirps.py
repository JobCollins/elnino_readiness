"""CHIRPS rainfall ingest (exposure pillar)."""

from __future__ import annotations

SOURCE = {
    "name": "CHIRPS",
    "provider": "UCSB Climate Hazards Center",
    "url": "https://www.chc.ucsb.edu/data/chirps",
    "resolution": "0.05deg (~5km)",
    "cadence": "pentad/monthly",
}


def load_rainfall_anomaly(*args, **kwargs):
    raise NotImplementedError(
        "Implement CHIRPS ingest: download rasters, compute SPI vs climatology, "
        "aggregate to admin units. See SOURCE for access details."
    )
