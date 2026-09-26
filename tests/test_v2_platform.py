"""
Automated Integration and Functional Test Suite for Panama PortOps-AI v2.0
Validates all endpoints of the Master Implementation Plan:
Health probes, Auth/IAM, RBAC/ABAC, Data Quality Gates, Feature Store, Models, Simulations, WORM Ledger.
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import sys
import re
from pathlib import Path
import pytest
import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
BASE_URL = "http://127.0.0.1:8000"


def get_root_credentials():
    """Extracts CSPRNG root credentials generated during bootstrap."""
    cred_file = ROOT_DIR / ".bootstrap" / "root-credentials.txt"
    if not cred_file.exists():
        pytest.skip(".bootstrap/root-credentials.txt not found")
    content = cred_file.read_text(encoding="utf-8")
    u_match = re.search(r"(?:Username|Usuario):\s+(root_\w+)", content)
    p_match = re.search(r"(?:Password|Password Temporal):\s+([^\r\n]+)", content)
    if not u_match or not p_match:
        pytest.fail("Could not parse root credentials file")
    return u_match.group(1), p_match.group(1).strip()


def get_root_session():
    """Performs full root login including MFA verification when enabled."""
    username, password = get_root_credentials()
    login_res = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": username, "password": password},
        timeout=5
    )
    data = login_res.json()
    if data.get("mfa_required"):
        import sqlite3, base64, struct, time, hmac, hashlib
        conn = sqlite3.connect(ROOT_DIR / "data" / "enterprise_db" / "portops_platform.db")
        cursor = conn.cursor()
        cursor.execute("SELECT mfa_secret FROM users WHERE username = ?;", (username,))
        row = cursor.fetchone()
        conn.close()
        secret_b32 = row[0]
        pad_len = (8 - len(secret_b32) % 8) % 8
        key = base64.b32decode(secret_b32 + "=" * pad_len, casefold=True)
        t = int(time.time() // 30)
        msg = struct.pack(">Q", t)
        h = hmac.new(key, msg, hashlib.sha1).digest()
        offset = h[-1] & 0x0F
        totp_int = (struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
        totp_code = f"{totp_int:06d}"

        mfa_res = requests.post(
            f"{BASE_URL}/api/v1/auth/mfa/verify",
            json={"temp_token": data["temp_token"], "totp_code": totp_code},
            timeout=5
        )
        return mfa_res.json(), username
    return data, username


def test_health_live():
    res = requests.get(f"{BASE_URL}/health/live", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "alive"
    assert "Panamá PortOps-AI" in data["service"]


def test_health_ready():
    res = requests.get(f"{BASE_URL}/health/ready", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "READY"
    assert data["database_connected"] is True


def test_health_dependencies():
    res = requests.get(f"{BASE_URL}/health/dependencies", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["platform_db"]["tables_count"] >= 10
    assert "users" in data["platform_db"]["tables"]
    assert "audit_ledger_worm" in data["platform_db"]["tables"]


def test_health_version():
    res = requests.get(f"{BASE_URL}/health/version", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["version"] == "1.0.0"
    assert "Miguel Benítez" in data["author"]


def test_auth_login_and_me():
    data, username = get_root_session()
    assert "session_token" in data
    assert data["user"]["username"] == username
    assert "root" in data["roles"]
    assert len(data["permissions"]) >= 25

    token = data["session_token"]

    # Test /api/v1/auth/me with Bearer token
    me_res = requests.get(
        f"{BASE_URL}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["username"] == username
    assert me_data["is_root"] is True


def test_auth_simulate_role():
    data, _ = get_root_session()
    token = data["session_token"]

    sim_res = requests.post(
        f"{BASE_URL}/api/v1/auth/simulate-role",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_role": "port_operator"},
        timeout=5
    )
    assert sim_res.status_code == 200
    data = sim_res.json()
    assert data["simulated_role"]["role_id"] == "port_operator"
    assert "forecast.read" in data["permissions"]


def test_roles_and_permissions_catalog():
    roles_res = requests.get(f"{BASE_URL}/api/v1/roles", timeout=5)
    assert roles_res.status_code == 200
    assert roles_res.json()["total_roles"] == 12

    perms_res = requests.get(f"{BASE_URL}/api/v1/permissions", timeout=5)
    assert perms_res.status_code == 200
    assert perms_res.json()["total_permissions"] == 31


def test_data_platform_quality_gates():
    res = requests.get(f"{BASE_URL}/api/v1/data/quality/summary", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["all_gates_passed"] is True
    assert data["overall_quality_score"] == 1.0
    assert len(data["gate_results"]) == 5

    # Run dynamic validation
    val_res = requests.post(f"{BASE_URL}/api/v1/data/quality/validate", timeout=10)
    assert val_res.status_code == 200
    assert val_res.json()["status"] == "PASSED"


def test_data_manifest_and_sources():
    sources_res = requests.get(f"{BASE_URL}/api/v1/data/sources", timeout=5)
    assert sources_res.status_code == 200
    sources = sources_res.json()["sources"]
    assert len(sources) >= 4

    manifest_res = requests.get(f"{BASE_URL}/api/v1/data/catalog/manifest", timeout=5)
    assert manifest_res.status_code == 200
    m = manifest_res.json()["manifest"]
    assert m["months_count"] >= 130
    assert len(m["schema_hash"]) == 64
    assert len(m["content_hash"]) == 64


def test_features_catalog():
    res = requests.get(f"{BASE_URL}/api/v1/features/catalog", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["total_features"] >= 8
    assert any(f["name"] == "teu_lag_1" for f in data["features"])


def test_models_benchmark_and_registry():
    bench_res = requests.get(f"{BASE_URL}/api/v1/models/benchmark", timeout=5)
    assert bench_res.status_code == 200
    bench_data = bench_res.json()
    assert "LightGBM" in bench_data["champion_algorithm"]
    assert len(bench_data["benchmark_comparison"]) >= 4

    reg_res = requests.get(f"{BASE_URL}/api/v1/models/registry", timeout=5)
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["models_count"] >= 1


def test_simulations_and_worm():
    data, _ = get_root_session()
    token = data["session_token"]

    # Run simulation
    sim_res = requests.post(
        f"{BASE_URL}/api/v1/simulations/run",
        headers={"Authorization": f"Bearer {token}"},
        json={"port": "Puerto Balboa", "horizon_months": 3, "paths": 500, "shock_scenario": "baseline"},
        timeout=10
    )
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert "expected_volume_p50_teus" in sim_data["results"]
    assert "audit_certification" in sim_data
    assert "worm_block_hash" in sim_data["audit_certification"]

    # Verify WORM chain
    worm_res = requests.get(f"{BASE_URL}/api/v1/audit/worm/verify", timeout=5)
    assert worm_res.status_code == 200
    worm_data = worm_res.json()
    assert worm_data["verification"]["valid"] is True

    # Audit events
    events_res = requests.get(f"{BASE_URL}/api/v1/audit/events", timeout=5)
    assert events_res.status_code == 200
    assert len(events_res.json()["events"]) >= 1


def test_telemetry_and_feedback():
    data, _ = get_root_session()
    token = data["session_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Check summary
    sum_res = requests.get(f"{BASE_URL}/api/v1/telemetry/summary", timeout=5)
    assert sum_res.status_code == 200
    s_data = sum_res.json()
    assert "total_inferences" in s_data
    assert "active_compute_device" in s_data
    assert "avg_latency_ms" in s_data

    # 2. Trigger reasoning chat to get a request_id
    chat_res = requests.post(
        f"{BASE_URL}/api/v1/agents/reasoning-chat",
        json={"query": "Proyección y normas aduaneras para contenedores en Puerto Balboa"},
        timeout=10
    )
    assert chat_res.status_code == 200
    c_data = chat_res.json()
    req_id = c_data["request_id"]
    assert req_id.startswith("req_")

    # 3. Submit feedback
    fb_res = requests.post(
        f"{BASE_URL}/api/v1/telemetry/feedback",
        headers=headers,
        json={
            "request_id": req_id,
            "rating_score": 5,
            "is_positive": 1,
            "feedback_category": "ACCURACY",
            "comments": "Auditoría automatizada conforme a Ley 6 de 2002."
        },
        timeout=5
    )
    assert fb_res.status_code == 200
    assert fb_res.json()["status"] == "FEEDBACK_RECORDED"

    # 4. Check telemetry logs as root
    logs_res = requests.get(f"{BASE_URL}/api/v1/telemetry/logs", headers=headers, timeout=5)
    assert logs_res.status_code == 200
    l_data = logs_res.json()
    assert l_data["total_records"] >= 1
    assert any(log["request_id"] == req_id for log in l_data["logs"])
