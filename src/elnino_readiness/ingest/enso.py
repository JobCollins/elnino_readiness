"""ENSO seasonal-signal ingest (exposure pillar)."""

from __future__ import annotations

SOURCE = {
    "name": "ENSO forecast",
    "provider": "IRI Columbia / NOAA CPC",
    "url": "https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/",
    "resolution": "basin scale (Nino 3.4)",
    "cadence": "monthly",
}


def load_enso_signal(*args, **kwargs):
    raise NotImplementedError(
        "Implement ENSO ingest: pull latest forecast probabilities to weight the "
        "seasonal storyline. See SOURCE for access details."
    )
