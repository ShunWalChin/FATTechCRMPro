"""One copy of the outbound destination check; a second copy is a second chance to forget a reserved range.

Both the n8n connection and any future external-request node let an operator point this server at an
arbitrary URL, so they share this module.
"""
import ipaddress
import socket
from urllib.parse import urlsplit


class OutboundUrlError(ValueError):
    """The destination is not a legitimate public HTTPS endpoint."""


def is_public_address(address: str) -> bool:
    """`is_global` also rejects CGNAT 100.64/10 and the documentation ranges that a hand-written
    octet table forgets; an IPv4-mapped IPv6 address is unwrapped before the test."""
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError:
        return False
    if isinstance(parsed, ipaddress.IPv6Address) and parsed.ipv4_mapped:
        parsed = parsed.ipv4_mapped
    return parsed.is_global


def resolved_addresses(host: str, port: int, resolver=socket.getaddrinfo) -> list[str]:
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        return [host]
    try:
        return [info[4][0] for info in resolver(host, port, proto=socket.IPPROTO_TCP)]
    except OSError as exc:
        raise OutboundUrlError("O host do destino não pôde ser resolvido") from exc


def assert_safe_outbound_url(value: str, *, resolver=socket.getaddrinfo) -> str:
    """Scheme, credentials and destination network.

    Resolution happens here and the connection happens later, so a DNS rebinding window stays open;
    closing it would require pinning the address in the HTTP client. The check still blocks the common
    case, which is pointing straight at a metadata endpoint or an internal host.
    """
    url = urlsplit(value)
    if url.scheme != "https":
        raise OutboundUrlError("O destino precisa usar HTTPS")
    if url.username or url.password or url.fragment:
        raise OutboundUrlError("A URL não pode conter credenciais ou fragmento")
    host = url.hostname
    if not host:
        raise OutboundUrlError("URL de destino inválida")
    addresses = resolved_addresses(host.lower(), url.port or 443, resolver)
    if not addresses or any(not is_public_address(address) for address in addresses):
        raise OutboundUrlError("O host resolve para uma rede privada ou reservada")
    return value
