"""SSRF-guarded HTTP GET with a response-size cap (issue #12).

The web collector fetches URLs auto-discovered from an untrusted resume, so a crafted
resume could point HireGauge at internal/cloud-metadata endpoints (``169.254.169.254``,
``localhost``, RFC1918 ranges) or return a huge body to exhaust memory. :func:`safe_get`:

- allows only ``http``/``https`` schemes,
- resolves the host and refuses private/loopback/link-local/reserved/multicast IPs
  **before** connecting, re-validating on every redirect hop (redirects are followed
  manually so a 3xx to an internal address can't slip through), and
- streams the body and stops at a byte cap instead of materializing the whole response.

Note: host resolution happens just before the request, so a determined DNS-rebinding
attacker could still race the connect (TOCTOU). Pinning the connection to the validated
IP would close that; it's out of scope here but the residual risk is documented.
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx

MAX_BYTES = 3 * 1024 * 1024  # 3 MB
MAX_REDIRECTS = 3
DEFAULT_TIMEOUT = 12.0


class UnsafeURLError(Exception):
    """Raised when a URL's scheme or resolved address is not allowed."""


@dataclass
class FetchResult:
    status_code: int
    headers: httpx.Headers
    text: str
    truncated: bool


def resolve_host(host: str, port: int) -> list[str]:
    """Return all IPs a host resolves to. Isolated so tests can monkeypatch resolution."""
    infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    return [info[4][0] for info in infos]


def _blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def validate_url(url: str) -> None:
    """Raise :class:`UnsafeURLError` unless ``url`` is http(s) to a public address."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise UnsafeURLError(f"scheme not allowed: {parts.scheme or '(none)'!r}")
    host = parts.hostname
    if not host:
        raise UnsafeURLError("URL has no host")

    # Host may be an IP literal — check it directly, no DNS.
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None:
        if _blocked(ip):
            raise UnsafeURLError(f"blocked address: {host}")
        return

    port = parts.port or (443 if parts.scheme == "https" else 80)
    try:
        addrs = resolve_host(host, port)
    except OSError as exc:
        raise UnsafeURLError(f"cannot resolve host: {host}") from exc
    if not addrs:
        raise UnsafeURLError(f"cannot resolve host: {host}")
    # Block if ANY resolved address is internal (defeats split-horizon tricks).
    for addr in addrs:
        if _blocked(ipaddress.ip_address(addr)):
            raise UnsafeURLError(f"blocked address for {host}: {addr}")


def _read_capped(resp: httpx.Response, max_bytes: int) -> FetchResult:
    chunks: list[bytes] = []
    total = 0
    truncated = False
    for chunk in resp.iter_bytes():
        chunks.append(chunk)
        total += len(chunk)
        if total >= max_bytes:
            truncated = True
            break
    raw = b"".join(chunks)[:max_bytes]
    encoding = resp.encoding or "utf-8"
    try:
        text = raw.decode(encoding, errors="replace")
    except LookupError:
        text = raw.decode("utf-8", errors="replace")
    return FetchResult(resp.status_code, resp.headers, text, truncated)


def safe_get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int = MAX_BYTES,
    max_redirects: int = MAX_REDIRECTS,
) -> FetchResult:
    """SSRF-guarded GET with a body cap. Validates the host before each hop and follows
    redirects manually so every target is re-validated. Raises :class:`UnsafeURLError` for
    a disallowed target, or an ``httpx`` error on transport failure."""
    current = url
    with httpx.Client(follow_redirects=False, timeout=timeout, headers=headers) as client:
        for _ in range(max_redirects + 1):
            validate_url(current)
            with client.stream("GET", current) as resp:
                if resp.is_redirect:
                    location = resp.headers.get("location")
                    if not location:
                        return _read_capped(resp, max_bytes)
                    current = urljoin(current, location)
                    continue
                return _read_capped(resp, max_bytes)
    raise UnsafeURLError(f"too many redirects (>{max_redirects})")
