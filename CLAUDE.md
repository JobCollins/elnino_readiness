# CLAUDE.md — El Niño Readiness Index

Context for Claude Code working in this repo. Read this first.

## What this project is

A composite **readiness-vs-exposure index** for the **Greater Horn of Africa (IGAD region)**, built to direct scarce anticipatory-action financing ahead of the 2026–27 El Niño. The headline signal is the *gap* between how exposed a place is and how ready it is to respond.

The full rationale, methodology and data map live in `docs/` (concept note + data-source matrix). Read them before making design decisions.

## Core model

Three pillars, each scored 0–100 per area:

- **Exposure / hazard** — the El Niño footprint (rainfall anomaly, vegetation stress, seasonal signal). A *borrowed* layer; don't reinvent it.
- **Vulnerability** — underlying fragility (poverty, nutrition, prior IPC phase). Also borrowed.
- **Readiness** — the differentiator: is anticipatory financing, planning, prepositioning and last-mile capacity actually in place? Mostly **hand-compiled and must be sourced/documented**.

Headline metric: **`gap = exposure − readiness`**. High positive gap = high exposure, low readiness = the "act first" group. See `src/elnino_readiness/index/composite.py`.

## Resolution principle

Admin-1 (province) is the **floor**; the design target is **admin-2 (district)**, and ward/livelihood-zone in priority hotspots. Use a **variable-resolution** approach: take each layer as fine as its data supports, aggregate transparently, and carry a confidence flag per unit rather than forcing one uniform grid. Finer resolution is the whole point — country-level scores hide what responders act on.

## Repo layout

```
config/            config.example.yaml (copy to config.yaml), priority_areas.yaml
data/seed/         illustrative_scores.csv — SYNTHETIC placeholder data
data/{raw,interim,processed}/   real data (gitignored)
src/elnino_readiness/
  ingest/          data-source connectors (chirps, enso, inform) — STUBS w/ SOURCE metadata
  pillars/         exposure / vulnerability / readiness scorers — pass-through placeholders
  index/composite.py   gap, priority tiers, quadrants (the real logic + tests)
  viz/map.py       quadrant scatter (works) + choropleth (stub, needs geo extras)
  cli.py           end-to-end entry point
tests/             pytest
docs/              concept note (.docx) + data-source matrix (.xlsx)
```

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # add ".[geo]" when implementing real ingest
python -m elnino_readiness.cli    # runs on seed data → outputs/
pytest -q
```

## Conventions

- Python ≥3.10, `src/` layout, type hints, small pure functions.
- Format/lint with `ruff`. Keep functions testable and side-effect-free where possible; I/O lives in `ingest/` and `cli.py`.
- Every new formula or threshold gets a test in `tests/`.
- **Never fabricate data.** Synthetic values live only in `data/seed/` and must stay labelled illustrative. Real pillar data must cite its source (use the `SOURCE` dict pattern in `ingest/`).
- The readiness layer is auditable by design — keep its sub-indicators explicit (see `pillars/readiness.py`) and document where each score came from.

## Roadmap (Phase 0)

Build in this order; each step should keep `pytest` green:

1. **Boundaries** — load admin-1/2 geometries for the priority countries; establish the canonical `area_id` join key.
2. **Exposure ingest** — implement `ingest/chirps.py` (rainfall anomaly/SPI) and wire `pillars/exposure.py`; population-weight with WorldPop.
3. **Vulnerability** — pull INFORM Subnational + IPC phase into `pillars/vulnerability.py`.
4. **Readiness** — hand-compile the sub-indicators per unit for the priority set; document sources.
5. **Composite + confidence** — extend `composite.py` with pillar weighting and a per-unit confidence flag.
6. **Choropleth** — implement `viz/map.py::plot_choropleth` (diverging ramp on `gap`).

Phase 1: data pipeline + living dashboard. Phase 2: extend to Southern Africa (framework transfers directly).

## Guardrails

- El Niño interacts with the Indian Ocean Dipole, conflict and price shocks — frame outputs as El Niño-*season* readiness, not sole causation.
- Prefer plugging into existing regional infrastructure (ICPAC/IGAD trigger matrices) over standalone reinvention.
