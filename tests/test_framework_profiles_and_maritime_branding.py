"""
Test Suite: Framework Profiles, Panama Maritime Branding, Infrastructure Configuration & Universal Selection Cursor.
Author: Desarrollado v1.0.0 Miguel Benítez • Ing. Miguel Antonio Benítez González (UTP) - GNU GPL-3.0
"""

import re
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from src.serving.api import app
from src.serving.v1_router import get_current_user_and_session

client = TestClient(app)
from tests.test_workspace_control_plane import control, login
STATIC_DIR = Path("src/serving/static")


@pytest.fixture
def admin_client(control):
    client,_=control
    login(client)
    return client


def test_framework_profile_get_and_post(admin_client):
    client = admin_client
    # 1. Test GET framework profile
    res_get = client.get("/api/v1/framework/profile")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["status"] == "success"
    assert "active_profile" in data_get
    assert len(data_get["available_profiles"]) == 4

    # 2. Test POST framework profile
    res_post = client.post("/api/v1/framework/profile", json={
        "profile_id": "terminal_portuaria",
        "updated_by": "test_suite"
    })
    assert res_post.status_code == 200
    data_post = res_post.json()
    assert data_post["status"] == "success"
    assert data_post["active_profile"] == "terminal_portuaria"
    assert "Terminal Portuaria" in data_post["profile_details"]["name"]


def test_infra_config_db_minio_wazuh(admin_client):
    client = admin_client
    assert client.post("/api/v1/framework/profile", json={"profile_id": "terminal_portuaria"}).status_code == 200
    # Test DB config
    res_db = client.post("/api/v1/infra/config/db", json={
        "db_type": "sqlite",
        "host": "127.0.0.1",
        "port": 5432,
        "db_name": "portops_platform.db",
        "username": "portops_admin",
        "password": "SecurePasswordTest2026!"
    })
    assert res_db.status_code == 200
    assert res_db.json()["status"] == "success"

    # Test MinIO config
    res_minio = client.post("/api/v1/infra/config/minio", json={
        "endpoint": "http://127.0.0.1:9000",
        "access_key": "minioadmin",
        "secret_key": "minioadmin",
        "buckets": "amp-bronze,amp-silver,amp-gold",
        "secure": False
    })
    assert res_minio.status_code == 200
    assert res_minio.json()["status"] == "success"

    # Test Wazuh config
    res_wazuh = client.post("/api/v1/infra/config/wazuh", json={
        "api_url": "https://127.0.0.1:55000",
        "api_user": "wazuh-wui",
        "api_password": "WazuhSecretPassword2026!",
        "agent_group": "portops-security-cluster"
    })
    assert res_wazuh.status_code == 200
    assert res_wazuh.json()["status"] == "success"

    # Test Infra configuration overview
    res_infra = client.get("/api/v1/infra/config")
    assert res_infra.status_code == 200
    configs = res_infra.json()["configs"]
    assert "database_config" in configs
    assert "minio_config" in configs
    assert "wazuh_config" in configs
    assert "framework_profile" in configs


def test_index_html_panama_maritime_branding_and_attribution():
    html_content = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    
    # Panama flag badge & branding
    assert "🇵🇦" in html_content
    assert "PANAMÁ" in html_content
    assert "PortOps-AI" in html_content
    
    # Author attribution
    assert "Miguel Benítez" in html_content
    assert "Ing. Miguel Antonio Benítez González (UTP)" in html_content
    assert "GNU GPL-3.0" in html_content

    # First-run modal Fase 0
    assert 'id="fr-tab-0"' in html_content
    assert 'id="fr-step-0"' in html_content
    assert "terminal_portuaria" in html_content
    assert "pyme_comercio" in html_content
    assert "investigacion_mlops" in html_content
    assert "auditoria_gobierno" in html_content

    # Table item detail modal
    assert 'id="table-row-detail-modal"' in html_content


def test_style_css_universal_cursor_pointer_and_select_rules():
    css_content = (STATIC_DIR / "css" / "style.css").read_text(encoding="utf-8")
    
    # Check universal cursor pointer
    assert "cursor: pointer !important;" in css_content
    
    # Check custom select styling
    assert "select {" in css_content or "select," in css_content
    assert "svg" in css_content.lower() # SVG chevron
    
    # Check profile card CSS
    assert ".fr-profile-card" in css_content
    assert ".fr-profile-grid" in css_content


def test_customs_rag_color_contrast():
    js_content = (STATIC_DIR / "js" / "customs_rag.js").read_text(encoding="utf-8")
    
    # Check that dark blue #0000ee is prevented by explicit cyan color in badge link
    assert "color: #00E5FF !important;" in js_content
    # Check that dark slate #64748B was upgraded to accessible token
    assert "#64748B" not in js_content
