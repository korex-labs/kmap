# Generation Rules

This document is the public contract for kmap generation behavior.

## Principles

- Kubernetes discovery and product configuration are the source inputs.
- `architecture.json` is renderer-neutral.
- Structurizr and LikeC4 renderers must read the same normalized model.
- Generated output must be deterministic for the same inputs.
- Examples and fixtures must use generic, sanitized, or mocked data only.

## Product Configs

Product configs live in `config/<product>.yaml` by default. They define product identity,
namespaces, discovery targets, resource links, and optional external mapping overrides.

Common mappings live in `config/common/external_mappings.yaml`.

## Outputs

By default, kmap writes:

```text
Likec4/<product>/
Structurizr/<product>/
Inventory/
artifacts/buckets/
.tmp/
```

Generated product outputs must not overwrite curated common layers such as `Likec4/common`.

## Data Modes

- `raw` may contain sensitive runtime values and should not be committed.
- `sanitized` is intended for normal generated output.
- `mocked` is intended for demos, tests, and public examples.

## Change Policy

When discovery, model, naming, relationship, or renderer behavior changes, update this document,
the relevant implementation, and tests in the same change set.
