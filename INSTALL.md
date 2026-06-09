# Installation

## Requirements

- Python 3.11 or newer.
- `kubectl` for live Kubernetes inspection.
- `helm` when Helm release discovery is needed.
- Docker for local LikeC4/Structurizr viewers and LikeC4 validation.

## Install from PyPI

```bash
pip install kmap
kmap --help
```

## Install from source

```bash
git clone https://github.com/<org>/kmap.git
cd kmap
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
```

## Project Layout

Run kmap from the architecture repository root. Defaults use the current working directory:

```text
config/
Likec4/
Structurizr/
Inventory/
artifacts/buckets/
.tmp/
```

Copy `kmap.yaml.example` to `kmap.yaml` when you need local defaults for viewer images, resource
recommendations, repository enrichment, storage labels, or inventory heuristics.

## Example

```bash
cp config/example.minimum.yaml config/my-product.yaml
kmap validate-config config/my-product.yaml
kmap run-all --config config/my-product.yaml --data-mode mocked --mock-seed demo --no-exec
```

Use `--data-mode sanitized` for normal committed generated output. Avoid committing raw Kubernetes payloads,
raw discovery reports, secrets, or local `.tmp` files.
