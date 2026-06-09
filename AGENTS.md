# Instructions for AI Agents and Coding Tools

These rules are mandatory for AI-assisted changes in the standalone kmap repository.

## Before Changing Code

- Read `README.md`, `INSTALL.md`, `DEVELOP.md`, `GENERATION_RULES.md`, and relevant tests.
- Inspect the owning module before editing.
- Check the working tree. Do not revert user changes.

## Commands

- Preferred CLI: `kmap ...`.
- Compatibility shim: `python kmap.py ...`.
- Do not assume a `tools/kmap` parent directory.

Run these after generator, renderer, config, or packaging changes:

```bash
python -m ruff check .
python -m ruff format --check .
make lint-complexity
python -m pytest
python -m pytest --cov --cov-report=term-missing
kmap validate-config config/example.minimum.yaml
kmap validate-config config/example.full.yaml
```

If Docker is available, also validate generated LikeC4/Structurizr examples.

## Compatibility

- Preserve existing CLI flags, environment variables, generated paths, and generated file names unless a breaking
  change is intentional and documented.
- Keep `kmap.py` thin.
- Keep dict/JSON model contracts stable.

## Public Data Safety

- Public examples must remain generic and sanitized.
- Do not add real company names, clusters, namespaces, domains, repository URLs, image registries, raw Kubernetes
  payloads, credentials, or screenshots containing private data.
- Run a secret/internal-data scan before adding fixtures, docs, examples, or generated outputs.

## Documentation

- Public documentation is English only.
- Update docs with behavior changes in the same change set.
- Update `GENERATION_RULES.md` when discovery, model, naming, relationship, or renderer rules change.

## Style

- Prefer small modules and pure helpers.
- Avoid broad rewrites without tests.
- Avoid dependencies unless declared in `pyproject.toml` and documented.
