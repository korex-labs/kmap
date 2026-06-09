# kmap

kmap discovers Kubernetes workloads, builds a normalized architecture model, and renders documentation for
Structurizr and LikeC4.

kmap is not a LikeC4-from-Structurizr converter. Kubernetes inspection and product configuration are the source
inputs; Structurizr and LikeC4 are renderer outputs.

## Install

```bash
pip install kmap
```

For development:

```bash
pip install -e '.[dev]'
```

## Quick start

Copy one of the generic examples:

```bash
cp config/example.minimum.yaml config/my-product.yaml
kmap validate-config config/my-product.yaml
kmap run-all --config config/my-product.yaml --data-mode mocked --mock-seed demo --no-exec
```

By default, run `kmap` from the project root. Paths resolve under the current directory:

```text
config/
Likec4/
Structurizr/
Inventory/
artifacts/buckets/
.tmp/
```

Tool-level defaults can be stored in `kmap.yaml`. Start from `kmap.yaml.example`.

## Common commands

```bash
kmap validate-config config/example.minimum.yaml
kmap render-inventory
kmap validate-likec4 --root Likec4
kmap validate-structurizr --root Structurizr
kmap view example-product
```

The source checkout also keeps `python kmap.py ...` as a compatibility shim.

## Documentation

- [INSTALL.md](INSTALL.md) - installation and runtime dependencies.
- [DEVELOP.md](DEVELOP.md) - development workflow and repository layout.
- [GENERATION_RULES.md](GENERATION_RULES.md) - model and renderer contract.
- [CONTRIBUTING.md](CONTRIBUTING.md) - contribution rules.
- [SECURITY.md](SECURITY.md) - security and data safety notes.
