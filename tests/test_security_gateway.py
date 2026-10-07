from fastapi.testclient import TestClient

from src.serving.api import app
from src.auth.bootstrap import BootstrapManager


def test_app_route_emits_browser_security_headers():
    client = TestClient(app)
    response = client.get("/app")

    assert response.status_code in {200, 404}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["permissions-policy"]
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-cache, no-store, must-revalidate"


def test_secure_proxy_enables_hsts_and_secure_session_cookie():
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "root_f2bbff", "password": BootstrapManager.DEFAULT_ROOT_PASSWORD},
        headers={"X-Forwarded-Proto": "https"},
    )

    assert response.status_code in {200, 401}
    assert response.headers["strict-transport-security"].startswith("max-age=31536000")
    if response.status_code == 200 and "set-cookie" in response.headers:
        cookie = response.headers["set-cookie"].lower()
        assert "httponly" in cookie
        assert "samesite=lax" in cookie
        assert "secure" in cookie
