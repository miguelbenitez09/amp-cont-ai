"""
Unit & Integration Tests for First-Run Setup & Mandatory Password Change Flow
Tests:
- Root first-run status check
- Mandatory password change with mismatch failure
- Mandatory password change with identical old password failure
- Successful double-entry root password change
- Creation of 3 mandatory admin accounts (SysAdmin, SecOpsAdmin, MlopsAdmin)
- Verification that setup is marked complete
"""

import pytest
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient
from src.serving.api import app
from src.auth.bootstrap import BootstrapManager, AuthenticationEngine
from src.serving.v1_router import get_db_conn

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_first_run_state():
    """Reset root to default unconfigured state and clean up test admins before and after each test."""
    def _reset():
        with get_db_conn() as conn:
            cursor = conn.cursor()
            pwd_hash, salt = AuthenticationEngine.hash_password(BootstrapManager.DEFAULT_ROOT_PASSWORD)
            cursor.execute("""
                UPDATE users 
                SET password_hash = ?, salt = ?, must_change_password = 1, mfa_enabled = 0, mfa_secret = NULL
                WHERE username = 'root'
            """, (pwd_hash, salt))
            
            for username in ["SysAdmin", "SecOpsAdmin", "MlopsAdmin"]:
                cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()
                if row:
                    uid = row[0]
                    cursor.execute("DELETE FROM user_roles WHERE user_id = ?", (uid,))
                    cursor.execute("DELETE FROM users WHERE user_id = ?", (uid,))
            conn.commit()
        # Keep the integration credential fixture synchronized with the
        # generated bootstrap secret so later API tests never depend on a
        # shared password or stale checked-in value.
        cred_file = Path(__file__).resolve().parent.parent / ".bootstrap" / "root-credentials.txt"
        if cred_file.exists():
            content = cred_file.read_text(encoding="utf-8")
            import re
            content = re.sub(r"Default Pass:\s+[^\r\n]+", f"Default Pass:  {BootstrapManager.DEFAULT_ROOT_PASSWORD}", content)
            cred_file.write_text(content, encoding="utf-8")
    _reset()
    yield
    _reset()



def test_first_run_status():
    """Verify first-run status endpoint returns proper schema."""
    resp = client.get("/api/v1/auth/first-run/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "root_exists" in data
    assert "root_must_change_password" in data
    assert "admins_configured" in data
    assert "missing_admins" in data

def test_first_run_password_mismatch():
    """Verify mismatched passwords fail."""
    resp = client.post("/api/v1/auth/first-run/change-root-password", json={
        "old_password": BootstrapManager.DEFAULT_ROOT_PASSWORD,
        "new_password": "NewSecurePass_2026!A",
        "confirm_password": "DifferentPass_2026!B"
    })
    assert resp.status_code == 400
    assert "coinciden" in resp.json()["detail"].lower()

def test_first_run_password_identical_to_old():
    """Verify identical password fails."""
    resp = client.post("/api/v1/auth/first-run/change-root-password", json={
        "old_password": BootstrapManager.DEFAULT_ROOT_PASSWORD,
        "new_password": BootstrapManager.DEFAULT_ROOT_PASSWORD,
        "confirm_password": BootstrapManager.DEFAULT_ROOT_PASSWORD
    })
    assert resp.status_code == 400
    assert "idéntica" in resp.json()["detail"].lower()

def test_first_run_create_admins_validation():
    """Verify short password validation for mandatory admins."""
    resp = client.post("/api/v1/auth/first-run/create-admins", json={
        "sysadmin": {"username": "SysAdmin", "password": "123"},
        "secops_admin": {"username": "SecOpsAdmin", "password": "SecOps_Pass_2026!"},
        "mlops_admin": {"username": "MlopsAdmin", "password": "Mlops_Pass_2026!"}
    })
    assert resp.status_code == 400
    assert "8 caracteres" in resp.json()["detail"]


def test_first_run_login_defers_mfa_until_password_rotation_and_setup_complete():
    """MFA cannot block the bootstrap operator before first-run setup is complete."""
    with get_db_conn() as conn:
        secret = AuthenticationEngine.generate_mfa_secret()
        conn.execute(
            "UPDATE users SET mfa_enabled = 1, mfa_secret = ?, must_change_password = 1 WHERE username = 'root';",
            (secret,),
        )
        conn.commit()

    resp = client.post("/api/v1/auth/login", json={
        "username": "root",
        "password": BootstrapManager.DEFAULT_ROOT_PASSWORD,
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["mfa_required"] is False
    assert data["mfa_deferred_until_setup_complete"] is True
    assert data["must_change_password"] is True
    assert "session_token" in data


def test_first_run_full_cycle():
    """Verify full first-run flow: password change and 3 admin creation."""
    # 1. Change root password
    resp = client.post("/api/v1/auth/first-run/change-root-password", json={
        "old_password": BootstrapManager.DEFAULT_ROOT_PASSWORD,
        "new_password": "PanamaRootSecure_2026!",
        "confirm_password": "PanamaRootSecure_2026!"
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    # 2. Create the 3 mandatory admins
    resp = client.post("/api/v1/auth/first-run/create-admins", json={
        "sysadmin": {"username": "SysAdmin", "password": "SysAdmin_Password_2026!", "email": "sysadmin@portops.pa"},
        "secops_admin": {"username": "SecOpsAdmin", "password": "SecOps_Password_2026!", "email": "secops@portops.pa"},
        "mlops_admin": {"username": "MlopsAdmin", "password": "Mlops_Password_2026!", "email": "mlops@portops.pa"}
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert len(data["admins"]) == 3

    # 3. Status check should confirm complete
    resp = client.get("/api/v1/auth/first-run/status")
    assert resp.status_code == 200
    status_data = resp.json()
    assert status_data["root_must_change_password"] is False
    assert status_data["admins_configured"] is True
    assert status_data["requires_first_run_setup"] is False
