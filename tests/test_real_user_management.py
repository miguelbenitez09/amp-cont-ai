"""
Unit & Integration Tests for Real SQLite User Management & Security UX
Validates:
- Real DB persistence (Zero mock) for User CRUD in SQLite (portops_platform.db)
- Password PBKDF2-HMAC-SHA256 hashing on user creation
- Root user protection from deletion
- Anti-paste, password matching and visibility toggle UI controls in served HTML
- Version standardization to v1.0.0
"""

import pytest
import sqlite3
import os
from fastapi.testclient import TestClient
from src.serving.api import app
from src.infrastructure.security.governance_panel import PanamaSecurityGovernancePanel
from src.auth.bootstrap import BootstrapManager
from src.serving.v1_router import get_db_conn

client = TestClient(app)


def admin_headers():
    for password in [
        BootstrapManager.DEFAULT_ROOT_PASSWORD,
        os.getenv("PORTOPS_ROOT_PASSWORD"),
        "PanamaRootSecure_2026!",
        "PortOpsSovereign2026!#",
    ]:
        if not password:
            continue
        response = client.post("/api/v1/auth/login", json={"username": "root", "password": password})
        if response.status_code == 200:
            return {"Authorization": f"Bearer {response.json()['session_token']}"}
    raise RuntimeError("Could not authenticate as root for test")


def test_list_real_users_from_db():
    """Verify GET /api/v1/auth/users returns real users from SQLite."""
    assert client.get("/api/v1/auth/users").status_code == 401
    resp = client.get("/api/v1/auth/users", headers=admin_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert "users" in data
    assert "total_users" in data
    assert data["total_users"] >= 1
    
    usernames = [u["username"] for u in data["users"]]
    assert "root" in usernames


def test_create_and_delete_real_user():
    """Verify POST and DELETE /api/v1/auth/users create and remove real users in DB."""
    test_user = "test_ops_analyst"
    
    # Clean up before
    headers = admin_headers()
    client.delete(f"/api/v1/auth/users/{test_user}", headers=headers)
    
    # 1. Create User
    create_resp = client.post("/api/v1/auth/users", headers=headers, json={
        "username": test_user,
        "full_name": "Analista Operativo de Prueba",
        "entity": "Autoridad Marítima de Panamá (AMP)",
        "role_id": "port_operator",
        "password": "TestPassword_2026!Strong"
    })
    assert create_resp.status_code == 200
    res_data = create_resp.json()
    assert res_data["status"] == "success"
    assert res_data["user"]["username"] == test_user

    # 2. Verify user exists in SQLite directly
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, password_hash, salt, is_active FROM users WHERE username = ?", (test_user,))
        row = cursor.fetchone()
        assert row is not None
        assert row["username"] == test_user
        assert len(row["password_hash"]) == 64  # SHA256 hex string
        assert len(row["salt"]) == 64  # 32 bytes hex string

    # 3. Duplicate user registration should fail
    dup_resp = client.post("/api/v1/auth/users", headers=headers, json={
        "username": test_user,
        "full_name": "Duplicado",
        "entity": "AMP",
        "role_id": "port_operator",
        "password": "AnotherPassword_2026!"
    })
    assert dup_resp.status_code == 400
    assert "ya existe" in dup_resp.json()["detail"].lower()

    # 4. Delete user
    del_resp = client.delete(f"/api/v1/auth/users/{test_user}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "success"

    # 5. Verify deletion in SQLite
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (test_user,))
        assert cursor.fetchone() is None


def test_root_user_is_protected_from_deletion():
    """Verify root cannot be deleted through the API."""
    resp = client.delete("/api/v1/auth/users/root", headers=admin_headers())
    assert resp.status_code == 400
    assert "protegido" in resp.json()["detail"].lower()


def test_ui_contains_anti_paste_eye_and_matching_elements():
    """Verify index.html contains anti-paste warnings, eye buttons, and matching indicators."""
    resp = client.get("/app")
    assert resp.status_code == 200
    html = resp.text

    # Anti-paste warning elements
    assert 'id="fr-paste-warning"' in html
    assert 'id="pwd-paste-warning"' in html
    assert 'id="new-user-paste-warning"' in html
    assert 'paste-warning-box' in html

    # Live password matching indicators
    assert 'id="fr-password-match-indicator"' in html
    assert 'id="pwd-match-indicator"' in html
    assert 'id="new-user-match-indicator"' in html
    assert 'password-match-indicator' in html

    # Eye toggle buttons
    assert 'btn-toggle-eye' in html
    assert 'togglePasswordEye' in html

    # Guest mode initial indicator
    assert 'Modo: Invitado' in html


def test_no_v2_string_in_scripts():
    """Verify all script tags and versions are standardized to v1.0.0."""
    resp = client.get("/app")
    assert resp.status_code == 200
    html = resp.text

    assert "?v=2.0.0" not in html
    assert "?v=1.0.0" in html
    assert "v1.0.0" in html
