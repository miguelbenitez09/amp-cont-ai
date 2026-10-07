from pathlib import Path

from fastapi.testclient import TestClient

from src.framework.app import create_app
from src.framework.settings import Settings


def test_canonical_first_login_rotation_and_logout(tmp_path: Path):
    app = create_app(Settings(mode="framework", state_dir=tmp_path))
    with TestClient(app) as client:
        credentials = (tmp_path / "bootstrap-credentials.json").read_text(encoding="utf-8")
        import json
        first = json.loads(credentials)
        response = client.post("/api/auth/login", json=first)
        assert response.status_code == 200
        csrf = response.json()["csrf_token"]
        assert response.json()["user"]["must_change_password"] is True

        rotated = client.post("/api/auth/password", headers={"X-CSRF-Token": csrf}, json={
            "current_password": first["password"],
            "new_password": "A-secure-rotation-password-2026!",
        })
        assert rotated.status_code == 200
        csrf = rotated.json()["csrf_token"]
        assert rotated.json()["user"]["must_change_password"] is False

        assert client.get("/api/auth/me").status_code == 200
        logged_out = client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
        assert logged_out.status_code == 200
        assert client.get("/api/auth/me").status_code == 401
