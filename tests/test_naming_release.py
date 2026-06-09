import re

from kmap.naming.release import matches_release_name, normalize_release_name


def test_matches_release_name_requires_non_empty_name_and_regex_match():
    match_re = re.compile(r"main")

    assert matches_release_name("release-main", match_re)
    assert not matches_release_name("release-api", match_re)
    assert not matches_release_name("", match_re)


def test_normalize_release_name_replaces_unsafe_runs_and_strips_edges():
    assert normalize_release_name(" hello world/api ") == "hello-world-api"
    assert normalize_release_name("...release_name-1...") == "...release_name-1..."
    assert normalize_release_name("///") == ""
