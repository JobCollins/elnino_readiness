"""INFORM Risk ingest (vulnerability pillar)."""

from __future__ import annotations

SOURCE = {
    "name": "INFORM Risk / INFORM Subnational",
    "provider": "EU JRC",
    "url": "https://drmkc.jrc.ec.europa.eu/inform-index",
    "resolution": "country + subnational",
    "cadence": "annual",
}


def load_inform(*args, **kwargs):
    raise NotImplementedError(
        "Implement INFORM ingest: download the index, map to target admin units. "
        "See SOURCE for access details."
    )
