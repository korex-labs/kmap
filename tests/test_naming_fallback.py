from kmap.naming.fallback import (
    apply_fallback_system_rewrites,
    canonical_fallback_system_name,
    collapse_project_wrapped_fallback_name,
)


def test_apply_fallback_system_rewrites_skips_invalid_and_tracks_applied_rules():
    assert apply_fallback_system_rewrites(
        "prod-demo-api",
        [
            {"match_regex": "(", "replace": ""},
            {"match_regex": "^prod-", "replace": ""},
            {"match_regex": "missing", "replace": "unused"},
        ],
    ) == ("demo-api", ["rewrite[1]"])


def test_canonical_fallback_system_name_respects_disabled_fallback():
    name, source = canonical_fallback_system_name(
        "prod-demo-api",
        "demo",
        "api",
        {"fallback": {"enabled": False}},
    )

    assert name == "prod-demo-api"
    assert source == {
        "raw_fallback_name": "prod-demo-api",
        "normalization_rules": [],
    }


def test_canonical_fallback_system_name_uses_unknown_for_punctuation_only_names():
    name, source = canonical_fallback_system_name("!!!", "demo", "api", {"fallback": {"enabled": True}})

    assert name == "unknown"
    assert source == {
        "raw_fallback_name": "!!!",
        "normalization_rules": [],
    }


def test_canonical_fallback_system_name_supports_custom_strip_tokens_and_rewrites():
    name, source = canonical_fallback_system_name(
        "blue-demo-api-worker-old",
        "demo",
        "api",
        {
            "fallback": {
                "rewrites": [{"match_regex": "-old", "replace": ""}],
                "strip_prefix_tokens": ["blue"],
                "strip_suffix_tokens": ["worker"],
            }
        },
    )

    assert name == "api"
    assert source["normalization_rules"] == [
        "rewrite[0]",
        "strip_env_prefix",
        "strip_env_suffix",
        "strip_product_prefix",
    ]


def test_canonical_fallback_system_name_can_skip_project_wrapper_collapse():
    name, source = canonical_fallback_system_name(
        "api-prod-api",
        "",
        "api",
        {"fallback": {"collapse_project_wrapped_names": False}},
    )

    assert name == "api-prod-api"
    assert source["normalization_rules"] == []


def test_collapse_project_wrapped_fallback_name_handles_repeat_marker_and_noop():
    assert collapse_project_wrapped_fallback_name(["api", "api"], ["api"], {"prod"}, {"prod"}) == (
        ["api"],
        "collapse_repeated_project",
    )
    assert collapse_project_wrapped_fallback_name(["api", "123", "api"], ["api"], {"prod"}, {"prod"}) == (
        ["api"],
        "collapse_project_wrapped_name",
    )
    assert collapse_project_wrapped_fallback_name(["api", "worker"], ["api"], {"prod"}, {"prod"}) == (
        ["api", "worker"],
        "",
    )
