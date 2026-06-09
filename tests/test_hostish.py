import pytest

from kmap.hostish import parse_hostish


def test_parse_hostish_rejects_private_ip_and_accepts_url():
    assert parse_hostish("10.0.0.1:5432") is None
    assert parse_hostish("https://api.example.com/path") == ("api.example.com", None, "/path")


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "true",
        "OFF",
        "null",
        "vault://secret/path",
        "12345",
        "30s",
        "api..example.com",
        ".api.example.com",
        "api.example.com.",
        "localhost",
        "127.0.0.1",
        "127.2.3.4",
        "http://[::1]:8080",
        "0.0.0.0",
        "feature-dev-service",
        "172.16.1.10",
        "192.168.1.10",
        "169.254.1.10",
        "10.10.10.10",
        "8.8.8.8:53",
        "1.2.3.4.5",
        "api.example.com:0",
        "api.example.com:65536",
        "https://",
    ],
)
def test_parse_hostish_rejects_non_dependency_values(value):
    assert parse_hostish(value) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ('"API.EXAMPLE.COM:443"', ("api.example.com", 443, None)),
        ("'postgres.example.com:5432/app'", ("postgres.example.com", 5432, "/app")),
        (
            "http://service.namespace.svc.cluster.local:8080/health",
            ("service.namespace.svc.cluster.local", 8080, "/health"),
        ),
        ("http://[2001:db8::1]:443/path", ("2001:db8::1", 443, "/path")),
    ],
)
def test_parse_hostish_accepts_host_like_values(value, expected):
    assert parse_hostish(value) == expected
