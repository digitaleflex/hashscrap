"""Fail-closed URL and DNS destination policy for outbound collection.

This module validates destinations before requests. It does not by itself pin a
validated DNS result to a socket; the downloader must enforce that boundary and
deployment egress rules must provide a second layer of protection.
"""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from urllib.parse import SplitResult, urljoin, urlsplit, urlunsplit

Resolver = Callable[[str, int], Iterable[str]]

DEFAULT_ALLOWED_PORTS = frozenset({80, 443})
BLOCKED_HOST_SUFFIXES = (".localhost", ".local", ".internal", ".test", ".invalid", ".example")
BLOCKED_HOSTS = frozenset({"localhost", "metadata.google.internal"})
CLOUD_METADATA_IPS = frozenset({"169.254.169.254", "100.100.100.200"})


@dataclass(frozen=True, slots=True)
class URLDecision:
    """Result of validating one URL destination."""

    allowed: bool
    reason: str
    normalized_url: str | None = None
    resolved_addresses: tuple[str, ...] = ()


def _system_resolver(host: str, port: int) -> tuple[str, ...]:
    """Resolve all socket addresses for a hostname."""
    records = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return tuple(sorted({str(record[4][0]) for record in records}))


def _is_public_address(value: str) -> bool:
    """Return whether an IP is globally routable and not a known metadata target."""
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False

    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
        address = address.ipv4_mapped

    return (
        str(address) not in CLOUD_METADATA_IPS
        and address.is_global
        and not address.is_private
        and not address.is_loopback
        and not address.is_link_local
        and not address.is_multicast
        and not address.is_unspecified
        and not address.is_reserved
    )


def _blocked_hostname(host: str) -> bool:
    normalized_host = host.rstrip(".").lower()
    return normalized_host in BLOCKED_HOSTS or any(
        normalized_host.endswith(suffix) for suffix in BLOCKED_HOST_SUFFIXES
    )


def _normalized_url(parsed: SplitResult) -> str:
    """Remove fragments, which are never sent to the remote server."""
    return urlunsplit((parsed.scheme.lower(), parsed.netloc, parsed.path or "/", parsed.query, ""))


def validate_url(
    url: str,
    *,
    resolver: Resolver = _system_resolver,
    allowed_ports: frozenset[int] = DEFAULT_ALLOWED_PORTS,
) -> URLDecision:
    """Validate HTTP(S), credentials, ports, and every resolved destination.

    The resolver is injectable so unit tests never need public Internet access.
    A hostname with mixed public and private answers is rejected as a whole.
    """
    try:
        parsed = urlsplit(url)
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return URLDecision(False, "malformed_url")

    if scheme not in {"http", "https"}:
        return URLDecision(False, "scheme_not_allowed")
    if not hostname or not parsed.netloc:
        return URLDecision(False, "hostname_required")
    if parsed.username is not None or parsed.password is not None:
        return URLDecision(False, "url_credentials_not_allowed")

    effective_port = port if port is not None else (443 if scheme == "https" else 80)
    if effective_port not in allowed_ports:
        return URLDecision(False, "port_not_allowed")
    if effective_port < 1 or effective_port > 65535:
        return URLDecision(False, "port_not_allowed")

    host = hostname.rstrip(".").lower()
    if _blocked_hostname(host):
        return URLDecision(False, "local_hostname_not_allowed")

    try:
        literal_address = ipaddress.ip_address(host)
    except ValueError:
        literal_address = None

    if literal_address is not None:
        addresses = (str(literal_address),)
    else:
        try:
            addresses = tuple(sorted(set(resolver(host, effective_port))))
        except (OSError, ValueError):
            return URLDecision(False, "dns_resolution_failed")
        if not addresses:
            return URLDecision(False, "dns_no_addresses")

    if any(not _is_public_address(address) for address in addresses):
        return URLDecision(False, "non_public_destination")

    return URLDecision(
        allowed=True,
        reason="allowed",
        normalized_url=_normalized_url(parsed),
        resolved_addresses=addresses,
    )


def validate_redirect(
    current_url: str,
    location: str,
    *,
    resolver: Resolver = _system_resolver,
    allowed_ports: frozenset[int] = DEFAULT_ALLOWED_PORTS,
) -> URLDecision:
    """Resolve a redirect against the current URL and revalidate its destination."""
    try:
        destination = urljoin(current_url, location)
    except ValueError:
        return URLDecision(False, "malformed_redirect")

    return validate_url(destination, resolver=resolver, allowed_ports=allowed_ports)
