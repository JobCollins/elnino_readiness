# El Niño Readiness Index — Greater Horn of Africa

A composite **readiness-vs-exposure index** to direct scarce anticipatory-action financing ahead of the 2026–27 El Niño. It borrows authoritative hazard and vulnerability layers and concentrates original effort on a **readiness** layer, so the output isolates the dangerous quadrant: high exposure, low readiness.

Headline metric: `gap = exposure − readiness`. See `CLAUDE.md` for the full model and `docs/` for the concept note and data-source matrix.

> Status: Phase 0 scaffold. It runs end-to-end on **synthetic seed data** (`data/seed/`) so the pipeline is green from day one. Real data connectors in `src/elnino_readiness/ingest/` are documented stubs.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m elnino_readiness.cli      # → outputs/readiness_index.csv + readiness_quadrant.png
pytest -q
```

## Layout

- `src/elnino_readiness/` — pipeline: `ingest/` (source connectors), `pillars/` (scorers), `index/composite.py` (the gap logic), `viz/`, `cli.py`
- `config/` — `config.example.yaml`, `priority_areas.yaml`
- `data/seed/` — illustrative placeholder scores (synthetic)
- `docs/` — concept note (.docx) and data-source matrix (.xlsx)
- `tests/` — pytest

## Next steps

The Phase 0 build order is in `CLAUDE.md` under Roadmap. Start with admin boundaries and the CHIRPS exposure connector.
