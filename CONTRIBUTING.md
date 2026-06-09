# Contributing

Thank you for improving kmap.

## Development setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
```

## Before opening a pull request

Run:

```bash
python -m ruff check .
python -m ruff format --check .
make lint-complexity
python -m pytest
python -m pytest --cov --cov-report=term-missing
kmap validate-config config/example.minimum.yaml
kmap validate-config config/example.full.yaml
```

Update `README.md`, `INSTALL.md`, `DEVELOP.md`, or `GENERATION_RULES.md` when behavior changes.

## Data safety

Do not add real company names, cluster names, domains, repository URLs, image registries, Kubernetes payloads,
or credentials to examples, tests, fixtures, generated output, screenshots, or documentation.
