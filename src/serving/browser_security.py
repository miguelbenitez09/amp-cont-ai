"""Browser request protection shared by the operational API."""
import hashlib
import hmac
import ipaddress
from urllib.parse import urlsplit

from fastapi import Request


def csrf_token_for_session(token: str) -> str:
    # Domain-separated digest; the bearer is high entropy and never exposed by /me.
    return hashlib.sha256(('portops-csrf-v1:' + token).encode()).hexdigest()


def request_origin(request: Request) -> str:
    scheme, host = request.url.scheme, request.headers.get('host', '')
    try:
        trusted_proxy = request.client and ipaddress.ip_address(request.client.host).is_loopback
    except ValueError:
        trusted_proxy = False
    if trusted_proxy:
        host = request.headers.get('x-forwarded-host', host)
        scheme = request.headers.get('x-forwarded-proto', scheme)
    return f'{scheme}://{host}'


def origin_matches(origin: str, expected: str) -> bool:
    try:
        supplied, target = urlsplit(origin), urlsplit(expected)
        if supplied.scheme not in {'http', 'https'} or supplied.username or supplied.password:
            return False
        if supplied.path or supplied.query or supplied.fragment or not supplied.hostname:
            return False
        return (supplied.scheme, supplied.hostname, supplied.port or (443 if supplied.scheme == 'https' else 80)) == (
            target.scheme, target.hostname, target.port or (443 if target.scheme == 'https' else 80))
    except ValueError:
        return False


def unsafe_browser_request(request: Request) -> bool:
    if request.method in {'GET', 'HEAD', 'OPTIONS'}:
        return False
    origin = request.headers.get('origin')
    if origin and not origin_matches(origin, request_origin(request)):
        return True
    if request.headers.get('sec-fetch-site') == 'cross-site':
        return True
    cookie = request.cookies.get('portops_session')
    # Bearer clients explicitly supply their credential and are not cookie-authenticated.
    credential_endpoints = {'/api/v1/auth/login', '/api/v1/auth/mfa/verify', '/api/v1/auth/first-run/change-root-password'}
    if cookie and request.url.path not in credential_endpoints and not request.headers.get('authorization', '').startswith('Bearer '):
        provided = request.headers.get('x-csrf-token', '')
        return not hmac.compare_digest(provided, csrf_token_for_session(cookie))
    return False
