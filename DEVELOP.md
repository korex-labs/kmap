# Development

## Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
```

## Checks

```bash
python -m ruff check .
python -m ruff format --check .
make lint-complexity
python -m pytest
python -m pytest --cov --cov-report=term-missing
kmap validate-config config/example.minimum.yaml
kmap validate-config config/example.full.yaml
```

## Layout

- `kmap/` contains the implementation.
- `tests/` contains unit tests.
- `config/` contains generic examples only.
- `.github/workflows/` contains GitHub Actions.

Keep modules small, keep generated output contracts stable, and update `GENERATION_RULES.md` when discovery,
model, naming, relationship, or renderer behavior changes.

## Data Safety

The public repository must never contain real company names, Kubernetes cluster names, namespaces, internal
domains, repository URLs, image registries, raw Kubernetes payloads, or credentials. Use generic examples and
mocked data.
