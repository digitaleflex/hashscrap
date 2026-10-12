"""Deterministic tests for URL policy; no public network calls are made."""

from __future__ import annotations

from collections.abc import Iterable

import pytest

from hashscrap.security.url_policy import validate_redirect, validate_url


def public_resolver(host: str, port: int) -> Iterable[str]:
    assert host == "example.org"
    assert port == 443
    return ("8.8.8.8",)


def test_allows_public_https_and_removes_fragment() -> None:
    decision = validate_url("https://example.org/path?q=1#section", resolver=public_resolver)

    assert decision.allowed is True
    assert decision.reason == "allowed"
    assert decision.normalized_url == "https://example.org/path?q=1"
    assert decision.resolved_addresses == ("8.8.8.8",)


@pytest.mark.parametrize(
    ("url", "reason"),
    [
        ("file:///etc/passwd", "scheme_not_allowed"),
        ("ftp://example.org/file", "scheme_not_allowed"),
        ("https:///missing-host", "hostname_required"),
        ("https://user:secret@example.org/", "url_credentials_not_allowed"),
        ("https://example.org:8443/", "port_not_allowed"),
        ("http://localhost/", "local_hostname_not_allowed"),
        ("http://service.internal/", "local_hostname_not_allowed"),
    ],
)
def test_rejects_invalid_url_shapes(url: str, reason: str) -> None:
    decision = validate_url(url, resolver=public_resolver)

    assert decision.allowed is False
    assert decision.reason == reason


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://10.0.0.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://100.100.100.200/",
        "http://[::1]/",
        "http://[fe80::1]/",
        "http://[::ffff:127.0.0.1]/",
    ],
)
def test_rejects_non_public_ip_literals(url: str) -> None:
    decision = validate_url(url)

    assert decision.allowed is False
    assert decision.reason == "non_public_destination"


def test_rejects_hostname_resolving_to_private_address() -> None:
    decision = validate_url(
        "https://example.org/",
        resolver=lambda host, port: ("8.8.8.8", "192.168.1.10"),
    )

    assert decision.allowed is False
    assert decision.reason == "non_public_destination"


def test_rejects_dns_failure() -> None:
    def failing_resolver(host: str, port: int) -> Iterable[str]:
        raise OSError("private resolver details should not be exposed")

    decision = validate_url("https://example.org/", resolver=failing_resolver)

    assert decision.allowed is False
    assert decision.reason == "dns_resolution_failed"
    assert "private resolver details" not in decision.reason


def test_rejects_empty_dns_answer() -> None:
    decision = validate_url("https://example.org/", resolver=lambda host, port: ())

    assert decision.allowed is False
    assert decision.reason == "dns_no_addresses"


def test_redirect_destination_is_revalidated() -> None:
    decision = validate_redirect(
        "https://example.org/start",
        "http://127.0.0.1/admin",
    )

    assert decision.allowed is False
    assert decision.reason == "non_public_destination"


def test_redirect_can_resolve_public_relative_location() -> None:
    decision = validate_redirect(
        "https://example.org/start",
        "/next",
        resolver=public_resolver,
    )

    assert decision.allowed is True
    assert decision.normalized_url == "https://example.org/next"
