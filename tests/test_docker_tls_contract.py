
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_production_compose_exposes_https_on_lan_with_tls_mounts():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    service = compose["services"]["portops-prod"]

    assert "prod-tls" in service["profiles"]
    assert "${PORTOPS_LAN_BIND:-0.0.0.0}:${PORTOPS_HTTPS_PORT:-8443}:8443" in service["ports"]
    assert service["environment"]["PORTOPS_SECURE_COOKIES"] == "1"
    assert service["environment"]["PORTOPS_ENABLE_HSTS"] == "1"
    assert "./.local/tls:/certs:ro" in service["volumes"]
    assert "no-new-privileges:true" in service["security_opt"]
    assert "ALL" in service["cap_drop"]


def test_production_dockerfile_runs_uvicorn_with_real_tls():
    dockerfile = (ROOT / "Dockerfile.production").read_text(encoding="utf-8")

    assert "EXPOSE 8443" in dockerfile
    assert '"--host", "0.0.0.0"' in dockerfile
    assert '"--port", "8443"' in dockerfile
    assert '"--ssl-keyfile", "/certs/portops.local.key"' in dockerfile
    assert '"--ssl-certfile", "/certs/portops.local.crt"' in dockerfile
    assert "PORTOPS_SECURE_COOKIES=1" in dockerfile
    assert "PORTOPS_ENABLE_HSTS=1" in dockerfile
    assert "libgomp1" in dockerfile
    assert "--root-user-action=ignore" in dockerfile
    assert "PIP_DISABLE_PIP_VERSION_CHECK=1" in dockerfile


def test_tls_generator_includes_lan_ip_discovery_and_san_generation():
    script = (ROOT / "scripts" / "generate_local_tls.py").read_text(encoding="utf-8")

    assert "ipconfig" in script
    assert "PORTOPS_TLS_EXTRA_IPS" in script
    assert "SubjectAlternativeName" in script
    assert "x509.IPAddress" in script
    assert "portops-local-ca.crt" in script



def test_model_runtime_dependencies_are_pinned_for_pickle_compatibility():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")

    for pinned in [
        "scikit-learn==1.8.0",
        "numpy==1.26.2",
        "pandas==2.1.4",
        "scipy==1.14.1",
        "lightgbm==4.6.0",
    ]:
        assert pinned in requirements
