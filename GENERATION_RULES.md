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

## Inventory Contracts

Cluster inventory JSON payloads use `schema_version: 1` and must remain backward compatible within that schema.

- Cluster fragments live under `Inventory/clusters/<cluster>/fragments/<fragment>.json`. They contain `cluster`,
  `fragment_id`, `generated_at`, `namespaces`, `repositories`, and `buckets`.
- Namespace state lives under `Inventory/clusters/<cluster>/state/namespaces/<namespace>.json`. It contains
  `cluster`, `namespace_name`, `last_seen_at`, a serialized `namespace` row, and deduplicated `buckets`.
- Aggregate cluster inventory lives at `Inventory/clusters/<cluster>/inventory.json`. It contains `cluster`,
  source `fragments`, source `states`, `last_seen_at`, merged `namespaces`, derived `repositories`, and merged
  `buckets`.

Namespace rows may include Kubernetes-discovered `labels` as a nested string mapping. Labels are discovered from
live namespace metadata and must not be read from product config. When merging rows, richer product/repository
metadata should win, but discovered labels should be preserved when the winning row does not carry labels.

Bucket rows are deduplicated by lowercased `namespace`, `repository`, `bucket`, `endpoint`, and `source_var`.
Fragment aggregation keeps the first duplicate bucket row; namespace state persistence keeps the newest duplicate
row for the same key.

## Data Modes

- `raw` may contain sensitive runtime values and should not be committed.
- `sanitized` is intended for normal generated output.
- `mocked` is intended for demos, tests, and public examples.

## Change Policy

When discovery, model, naming, relationship, or renderer behavior changes, update this document,
the relevant implementation, and tests in the same change set.
