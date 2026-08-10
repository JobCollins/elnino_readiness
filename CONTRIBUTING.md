# Contributing / dev setup

## One-time setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"        # add ".[geo]" when implementing real ingest
pip install pre-commit
pre-commit install             # runs ruff on every commit
```

## Everyday loop

```bash
python -m elnino_readiness.cli   # run the pipeline on seed data → outputs/
pytest -q                        # tests must stay green
ruff check . && ruff format .    # lint + format (pre-commit does this on commit)
pre-commit run --all-files       # run every hook manually
```

## Conventions

- Python ≥3.10, `src/` layout, type hints, small pure functions. Line length 100.
- Keep scoring functions pure and testable; I/O lives in `ingest/` and `cli.py`.
- **Every new formula or threshold gets a test** in `tests/`.
- **Never fabricate data.** Synthetic values live only in `data/seed/` and stay labelled illustrative; real pillar data cites its source via the `SOURCE` dict pattern in `ingest/`.
- Branch → commit small → open a PR. Keep `pytest` and `ruff` green before pushing.

See `CLAUDE.md` for the project model and the Phase 0 roadmap.
