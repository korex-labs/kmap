"""Shared discovery source priority helpers."""

SOURCE_RANK = {"VaultEnv": 4, "Env": 3, "Secret": 2, "ConfigMap": 1}


def source_rank(source: object) -> int:
    return SOURCE_RANK.get(str(source or ""), 0)


__all__ = ["SOURCE_RANK", "source_rank"]
