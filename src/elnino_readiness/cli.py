"""Command-line entry point.

Runs the pipeline end-to-end — either on illustrative seed data (default)
or on live CHIRPS + WorldPop data (``--live``).
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from .index.composite import compute_index
from .pillars.exposure import exposure_score
from .pillars.readiness import readiness_score
from .viz.map import plot_quadrant

DEFAULT_SEED = Path("data/seed/illustrative_scores.csv")

logger = logging.getLogger(__name__)


def run(seed: Path, outdir: Path) -> pd.DataFrame:
    """Seed-data pipeline (Phase 0 default)."""
    df = pd.read_csv(seed)
    df["exposure"] = exposure_score(df)
    df["readiness"] = readiness_score(df)
    idx = compute_index(df)
    outdir.mkdir(parents=True, exist_ok=True)
    idx.to_csv(outdir / "readiness_index.csv", index=False)
    plot_quadrant(idx, outdir / "readiness_quadrant.png")
    return idx


def run_live(
    year: int,
    month: int,
    admin_level: int,
    outdir: Path,
    cache_dir: Path = Path("data/raw"),
) -> pd.DataFrame:
    """Live pipeline: CHIRPS anomaly → pop-weighted zonal stats → exposure score."""
    from .ingest.boundaries import load_priority_boundaries
    from .ingest.chirps import load_rainfall_anomaly
    from .ingest.worldpop import merge_population
    from .ingest.zonal import zonal_stats

    logger.info("Loading admin-%d boundaries for priority countries…", admin_level)
    boundaries = load_priority_boundaries(admin_level, cache_dir=cache_dir / "boundaries")

    logger.info("Downloading CHIRPS anomaly for %d-%02d…", year, month)
    anomaly_path = load_rainfall_anomaly(year, month, cache_dir=cache_dir / "chirps")

    iso3_list = boundaries["country_iso3"].unique().tolist()
    logger.info("Downloading WorldPop for %d countries…", len(iso3_list))
    pop_path = merge_population(
        iso3_list,
        cache_dir=cache_dir / "worldpop",
        out_dir=Path("data/interim/worldpop"),
    )

    logger.info("Computing population-weighted zonal stats…")
    boundaries["rainfall_anomaly_pct"] = zonal_stats(boundaries, anomaly_path, pop_path)
    boundaries["exposure"] = exposure_score(boundaries)

    # Readiness placeholder — will be filled by Step 4
    if "readiness" not in boundaries.columns:
        boundaries["readiness"] = 50.0
        logger.warning("Using placeholder readiness=50 for all areas (Step 4 pending)")

    idx = compute_index(boundaries)
    outdir.mkdir(parents=True, exist_ok=True)
    idx.to_csv(outdir / "readiness_index.csv", index=False)
    plot_quadrant(idx, outdir / "readiness_quadrant.png")
    return idx


def main(argv=None):
    p = argparse.ArgumentParser(description="El Niño readiness index")
    p.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    p.add_argument("--outdir", type=Path, default=Path("outputs"))
    p.add_argument("--live", action="store_true", help="Use real CHIRPS + WorldPop data")
    p.add_argument("--year", type=int, default=2026, help="CHIRPS year (default: 2026)")
    p.add_argument("--month", type=int, default=6, help="CHIRPS month (default: 6)")
    p.add_argument(
        "--admin-level",
        type=int,
        default=1,
        choices=[1, 2],
        help="Admin level for boundaries (default: 1)",
    )
    args = p.parse_args(argv)

    if args.live:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
        idx = run_live(args.year, args.month, args.admin_level, args.outdir)
        label = f"Live output (CHIRPS {args.year}-{args.month:02d}, admin-{args.admin_level})"
    else:
        idx = run(args.seed, args.outdir)
        label = "Illustrative output (synthetic seed data)"

    cols = ["area_name", "exposure", "readiness", "gap", "priority_tier", "quadrant"]
    print(f"\n{label}:\n")
    print(idx[cols].to_string(index=False))
    print(
        f"\nWrote {args.outdir / 'readiness_index.csv'} "
        f"and {args.outdir / 'readiness_quadrant.png'}"
    )


if __name__ == "__main__":
    main()
