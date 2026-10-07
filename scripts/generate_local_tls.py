"""Generate a local CA and TLS certificate for LAN testing."""

from __future__ import annotations

import ipaddress
import os
import re
import socket
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


ROOT = Path(__file__).resolve().parents[1]
TLS_DIR = ROOT / ".local" / "tls"
CA_KEY = TLS_DIR / "portops-local-ca.key"
CA_CERT = TLS_DIR / "portops-local-ca.crt"
SERVER_KEY = TLS_DIR / "portops.local.key"
SERVER_CERT = TLS_DIR / "portops.local.crt"


def is_usable_local_ip(value: str) -> bool:
    try:
        parsed = ipaddress.ip_address(value.strip())
    except ValueError:
        return False
    return parsed.version == 4 and not parsed.is_loopback and not parsed.is_link_local


def add_ip(ips: set[str], value: str) -> None:
    value = value.strip()
    if value == "127.0.0.1" or is_usable_local_ip(value):
        ips.add(value)


def local_ips() -> list[str]:
    ips = {"127.0.0.1"}
    hostname = socket.gethostname()
    try:
        for info in socket.getaddrinfo(hostname, None, family=socket.AF_INET):
            add_ip(ips, info[4][0])
    except socket.gaierror:
        pass

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("8.8.8.8", 80))
            add_ip(ips, probe.getsockname()[0])
    except OSError:
        pass

    if os.name == "nt":
        try:
            ipconfig = subprocess.run(["ipconfig"], capture_output=True, text=True, check=False)
            for match in re.findall(r"IPv4[^:]*:\s*([0-9.]+)", ipconfig.stdout):
                add_ip(ips, match)
        except OSError:
            pass

    for raw_ip in os.environ.get("PORTOPS_TLS_EXTRA_IPS", "").split(","):
        if raw_ip.strip():
            add_ip(ips, raw_ip)

    return sorted(ips, key=lambda ip: tuple(int(part) for part in ip.split(".")))


def write_private_key(path: Path, key) -> None:
    path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )


def main() -> int:
    TLS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)

    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    ca_subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "PA"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Panama PortOps-AI Local CA"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Panama PortOps-AI Local Development CA"),
    ])
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_subject)
        .issuer_name(ca_subject)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=825))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(x509.KeyUsage(digital_signature=True, key_cert_sign=True, crl_sign=True, key_encipherment=False, content_commitment=False, data_encipherment=False, key_agreement=False, encipher_only=False, decipher_only=False), critical=True)
        .sign(ca_key, hashes.SHA256())
    )
    write_private_key(CA_KEY, ca_key)
    CA_CERT.write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))

    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    names = [
        x509.DNSName("localhost"),
        x509.DNSName("portops.local"),
    ]
    for ip in local_ips():
        names.append(x509.IPAddress(ipaddress.ip_address(ip)))

    server_subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "PA"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Panama PortOps-AI"),
        x509.NameAttribute(NameOID.COMMON_NAME, "portops.local"),
    ])
    server_cert = (
        x509.CertificateBuilder()
        .subject_name(server_subject)
        .issuer_name(ca_cert.subject)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=397))
        .add_extension(x509.SubjectAlternativeName(names), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .sign(ca_key, hashes.SHA256())
    )
    write_private_key(SERVER_KEY, server_key)
    SERVER_CERT.write_bytes(server_cert.public_bytes(serialization.Encoding.PEM))

    print("TLS local generado:")
    print(f"  CA:      {CA_CERT}")
    print(f"  Cert:    {SERVER_CERT}")
    print(f"  Key:     {SERVER_KEY}")
    print("SAN IPs:")
    for ip in local_ips():
        print(f"  https://{ip}:8443/app")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
