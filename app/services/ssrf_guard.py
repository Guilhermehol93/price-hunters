"""SSRF Protection and URL Validation Guard"""

import socket
import ipaddress
from urllib.parse import urlparse
from app.config import settings


class SSRFSecurityException(Exception):
    """Exceção levantada quando uma URL aponta para destinos privados ou proibidos."""
    pass


# Redes e faixas restritas / privadas
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),          # RFC 1918 Privada
    ipaddress.ip_network("127.0.0.0/8"),         # Loopback
    ipaddress.ip_network("169.254.0.0/16"),      # Link-local / Cloud Metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),       # RFC 1918 Privada
    ipaddress.ip_network("192.168.0.0/16"),      # RFC 1918 Privada
    ipaddress.ip_network("192.0.2.0/24"),        # Documentação (TEST-NET-1)
    ipaddress.ip_network("198.51.100.0/24"),     # Documentação (TEST-NET-2)
    ipaddress.ip_network("203.0.113.0/24"),      # Documentação (TEST-NET-3)
    ipaddress.ip_network("224.0.0.0/4"),         # Multicast
    ipaddress.ip_network("240.0.0.0/4"),         # Reservado
    ipaddress.ip_network("::1/128"),             # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),            # IPv6 Unique Local
    ipaddress.ip_network("fe80::/10"),           # IPv6 Link Local
]

BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "169.254.169.254",
    "instance-data",
}


def validate_target_url(url: str) -> str:
    """Valida se a URL fornecida é segura contra SSRF.

    Verifica protocolo (apenas HTTP/HTTPS), formato, resolução DNS e rejeita
    endereços privados, loopbacks, serviços de metadados em nuvem e hosts locais.
    """
    if not url or not isinstance(url, str):
        raise SSRFSecurityException("A URL informada é vazia ou inválida.")

    parsed = urlparse(url.strip())

    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFSecurityException(f"Esquema de URL não suportado: {parsed.scheme}. Apenas http e https são permitidos.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFSecurityException("Não foi possível identificar o hostname na URL fornecida.")

    hostname_clean = hostname.strip().lower()

    if hostname_clean in BLOCKED_HOSTNAMES:
        raise SSRFSecurityException(f"Acesso bloqueado ao hostname restrito: {hostname}")

    # Se a configuração explicitamente permitir IPs privados (apenas em testes de laboratório controlados)
    if settings.ALLOW_PRIVATE_IPS:
        return url

    # Resolver DNS e testar cada endereço IP retornado
    try:
        # Se já for um IP direto
        try:
            ip = ipaddress.ip_address(hostname_clean)
            _check_ip_safety(ip)
            return url
        except ValueError:
            pass

        # Resolução de nomes
        addr_infos = socket.getaddrinfo(hostname_clean, None)
        resolved_ips = set()
        for family, _, _, _, sockaddr in addr_infos:
            ip_str = sockaddr[0]
            resolved_ips.add(ipaddress.ip_address(ip_str))

        if not resolved_ips:
            raise SSRFSecurityException(f"O hostname {hostname} não pôde ser resolvido para nenhum endereço IP.")

        for ip in resolved_ips:
            _check_ip_safety(ip)

    except socket.gaierror as e:
        raise SSRFSecurityException(f"Falha ao resolver endereço DNS para o host {hostname}: {e}")

    return url


def _check_ip_safety(ip: ipaddress.IPv4Address | ipaddress.IPv6Address):
    if ip.is_loopback:
        raise SSRFSecurityException(f"Acesso a endereço loopback bloqueado por segurança: {ip}")
    if ip.is_private:
        raise SSRFSecurityException(f"Acesso a rede interna/privada bloqueado por segurança: {ip}")
    if ip.is_link_local:
        raise SSRFSecurityException(f"Acesso a endereço link-local bloqueado por segurança: {ip}")
    if ip.is_reserved:
        raise SSRFSecurityException(f"Acesso a endereço reservado bloqueado por segurança: {ip}")

    for net in BLOCKED_IP_NETWORKS:
        if ip in net:
            raise SSRFSecurityException(f"O endereço IP {ip} pertence a uma faixa bloqueada: {net}")
