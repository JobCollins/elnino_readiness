"""Command-line entry point for the Phase 0 scaffold.

Runs the pipeline end-to-end on illustrative seed data and writes a scored CSV
plus a quadrant chart. Replace the seed data with real pillar outputs as the
ingest connectors are implemented.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .index.composite import compute_index
from .pillars.exposure import exposure_score
from .pillars.readiness import readiness_score
from .viz.map import plot_quadrant

DEFAULT_SEED = Path("data/seed/illustrative_scores.csv")


def run(seed: Path, outdir: Path) -> pd.DataFrame:
    df = pd.read_csv(seed)
    df["exposure"] = exposure_score(df)
    df["readiness"] = readiness_score(df)
    idx = compute_index(df)
    outdir.mkdir(parents=True, exist_ok=True)
    idx.to_csv(outdir / "readiness_index.csv", index=False)
    plot_quadrant(idx, outdir / "readiness_quadrant.png")
    return idx


def main(argv=None):
    p = argparse.ArgumentParser(description="El Nino readiness index (Phase 0 scaffold)")
    p.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    p.add_argument("--outdir", type=Path, default=Path("outputs"))
    args = p.parse_args(argv)

    idx = run(args.seed, args.outdir)
    cols = ["area_name", "exposure", "readiness", "gap", "priority_tier", "quadrant"]
    print("\nIllustrative output (synthetic seed data):\n")
    print(idx[cols].to_string(index=False))
    print(
        f"\nWrote {args.outdir / 'readiness_index.csv'} "
        f"and {args.outdir / 'readiness_quadrant.png'}"
    )


if __name__ == "__main__":
    main()
