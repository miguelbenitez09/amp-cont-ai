"""
Unit Tests for Privacy & Anonymization Engine (Ley 81 de 2019),
Deterministic Reproducibility, Government RBAC Security, and MCP Souls.

Author: Desarrollado v1.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

import pytest
from fastapi.testclient import TestClient
from src.serving.api import app
from src.data.privacy.anonymizer import PanamaDataAnonymizerEngine
from src.models.training_presets import TrainingPresetManager
from src.models.reproducible_trainer import DeterministicModelReplicator
from src.infrastructure.security.governance_panel import PanamaSecurityGovernancePanel
from src.mcp.soul_manager import MCPSoulManager


client = TestClient(app)


class TestPanamaPrivacyAndAnonymization:
    def test_sensitive_dataset_trigger_identification(self):
        res1 = PanamaDataAnonymizerEngine.identify_dataset_sensitivity("manifiestos_aduanas_carga_2026.csv")
        assert res1["requires_anonymization"] is True
        assert res1["matched_triggers_count"] >= 1

        res2 = PanamaDataAnonymizerEngine.identify_dataset_sensitivity("acp_gatun_lake_levels_2026.csv")
        assert res2["requires_anonymization"] is False

    def test_ordered_anonymization_pipeline(self):
        sample = [
            {
                "id": "1",
                "consignatario_nombre": "Empresa Privada de Balboa Inc.",
                "cedula_representante": "8-456-7890",
                "ruc_fiscal": "12345-6-789012 DV 33",
                "pasaporte_capitan": "PA1234567",
                "factura_monto_fob": 75000.0,
                "puerto": "Puerto Balboa"
            }
        ]
        result = PanamaDataAnonymizerEngine.execute_ordered_pipeline("manifiesto_aduanero_privado.csv", sample)
        assert result["status"] == "success"
        assert "audit_certificate" in result
        assert result["audit_certificate"]["legal_compliance"] == "Ley 81 de 26 de marzo de 2019 de la República de Panamá"

        decon = result["decontaminated_sample"][0]
        # Check that sensitive fields are obscured
        assert decon["cedula_representante"].startswith("ANON_")
        assert decon["ruc_fiscal"].startswith("ANON_")
        assert decon["consignatario_nombre"].startswith("ANON_")
        assert decon["pasaporte_capitan"] == "[REDACTADO_LEY_81]"
        assert "USD" in decon["factura_monto_fob"]  # Bucketed


class TestModelPresetsAndReproducibility:
    def test_presets_catalog(self):
        presets = TrainingPresetManager.list_presets()
        assert len(presets) == 6
        preset_ids = {p["id"] for p in presets}
        assert "balanced_production" in preset_ids
        assert "conservative_anti_overfitting" in preset_ids
        assert "aggressive_shock_reaction" in preset_ids
        assert "resilient_quantile_stress" in preset_ids
        assert "ultra_low_latency_tree" in preset_ids
        assert "deep_additive_quantile" in preset_ids

    def test_deterministic_reproducibility_verification(self):
        cert = DeterministicModelReplicator.verify_reproducibility(seed=42)
        assert cert["status"] == "verified_deterministic"
        assert cert["seed_configured"] == 42
        assert cert["expected_metrics"]["wape"] == 0.0911
        assert cert["expected_metrics"]["r2_score"] == 0.9594
        assert "cross_machine_consistency" in cert


class TestGovernmentSecurityAndMCPSouls:
    def test_security_overview(self):
        overview = PanamaSecurityGovernancePanel.get_security_overview()
        assert overview["status"] == "operational"
        assert "tls_certificate" in overview
        assert overview["tls_certificate"]["protocol"] == "TLS 1.3 (RFC 8446)"
        assert overview["cookie_hardening"]["http_only"] is True
        assert len(overview["roles_matrix"]) >= 4

    def test_user_registration_and_session_revocation(self):
        reg = PanamaSecurityGovernancePanel.register_user(
            username="test_auditor_user",
            full_name="Auditor de Prueba",
            entity="Contraloría",
            role_id="compliance_auditor"
        )
        assert reg["status"] == "success"
        assert reg["user"]["username"] == "test_auditor_user"

        rev = PanamaSecurityGovernancePanel.revoke_all_sessions(reason="Prueba Unitaria")
        assert rev["status"] == "revoked"

    def test_mcp_souls_and_tool_execution(self):
        souls = MCPSoulManager.list_souls()
        assert len(souls) >= 3
        soul_ids = {s["id"] for s in souls}
        assert "auditor_maritimo" in soul_ids
        assert "operador_muelle" in soul_ids
        assert "cientifico_causal" in soul_ids

        # Test tool execution in JSON-RPC 2.0 format
        rpc = MCPSoulManager.execute_mcp_tool_rpc("compare_model_benchmarks", {}, soul_id="cientifico_causal")
        assert rpc["jsonrpc"] == "2.0"
        assert "result" in rpc
        assert rpc["result"]["tool"] == "compare_model_benchmarks"


class TestNewServingApiEndpoints:
    def test_get_training_parameters(self):
        res = client.get("/api/models/training-parameters")
        assert res.status_code == 200
        d = res.json()
        assert d["status"] == "success"
        assert "champion_model_architecture" in d
        assert "datasets_provenance_and_extraction" in d
        assert len(d["datasets_provenance_and_extraction"]["official_sources"]) >= 4

    def test_get_model_presets(self):
        res = client.get("/api/models/presets")
        assert res.status_code == 200
        d = res.json()
        assert d["total_presets"] >= 6

    def test_post_custom_preset_and_fetch(self):
        payload = {
            "id": "unit_test_preset",
            "name": "Unit Test Custom Preset",
            "description": "Preset creado para pruebas automatizadas",
            "base_algorithm": "lightgbm",
            "hyperparameters": {
                "learning_rate": 0.04,
                "n_estimators": 100,
                "max_depth": 5
            },
            "target_application": "Pruebas unitarias de extensibilidad"
        }
        res = client.post("/api/models/presets", json=payload)
        assert res.status_code == 200
        d = res.json()
        assert d["status"] == "success"

        res_fetch = client.get("/api/models/presets/unit_test_preset")
        assert res_fetch.status_code == 200
        assert res_fetch.json()["preset"]["name"] == "Unit Test Custom Preset"

    def test_database_test_connection(self):
        res = client.post("/api/infrastructure/database/test-connection", json={"engine": "duckdb"})
        assert res.status_code == 200
        d = res.json()
        assert "duckdb" in d["engine"].lower()
        assert d["status"] in ["online", "success", "container_configured"]
        assert d["latency_ms"] >= 0.0

    def test_langgraph_route(self):
        res = client.post("/api/mcp/langgraph-route", json={"query": "¿Qué exige la Ley 56 sobre concesiones de muelles?"})
        assert res.status_code == 200
        d = res.json()
        assert d["selected_soul"]["id"] in ["auditor_maritimo", "operador_muelle", "cientifico_causal", "ingesta_master"]
        assert len(d["langgraph_dag_trace"]) >= 2

    def test_verify_permission(self):
        # root has all permissions
        res = client.post("/api/admin/verify-permission", json={"username": "root", "permission": "retrain_model"})
        assert res.status_code == 200
        assert res.json()["allowed"] is True

        # port_operator cannot retrain model
        res2 = client.post("/api/admin/verify-permission", json={"username": "operador_balboa", "permission": "retrain_model"})
        assert res2.status_code == 200
        assert res2.json()["allowed"] is False

    def test_first_run_status(self):
        res = client.get("/api/admin/first-run-status")
        assert res.status_code == 200
        d = res.json()
        assert "is_first_run" in d
        assert "cluster_state" in d

    def test_post_reproducible_train(self):
        res = client.post("/api/models/reproducible-train", json={"seed": 42, "preset_id": "balanced_production"})
        assert res.status_code == 200
        d = res.json()
        assert d["status"] == "verified_deterministic"

    def test_get_privacy_rules(self):
        res = client.get("/api/privacy/anonymization-rules")
        assert res.status_code == 200
        d = res.json()
        assert "sensitive_dataset_triggers" in d

    def test_post_simulate_anonymization(self):
        payload = {
            "dataset_name": "aduanas_contribuyentes_test.csv"
        }
        res = client.post("/api/privacy/simulate-anonymization", json=payload)
        assert res.status_code == 200
        d = res.json()
        assert d["status"] == "success"
        assert "audit_certificate" in d

    def test_get_admin_governance(self):
        res = client.get("/api/admin/governance")
        assert res.status_code == 200
        d = res.json()
        assert d["status"] == "operational"

    def test_post_admin_users(self):
        payload = {
            "username": "portal_admin_unit",
            "full_name": "Administrador de Portal",
            "entity": "AMP",
            "role_id": "platform_admin"
        }
        res = client.post("/api/admin/users", json=payload)
        assert res.status_code == 200
        assert res.json()["status"] == "success"

    def test_post_revoke_sessions(self):
        res = client.post("/api/admin/revoke-sessions", json={"reason": "Auditoría Regular"})
        assert res.status_code == 200
        assert res.json()["status"] == "revoked"

    def test_get_mcp_souls(self):
        res = client.get("/api/mcp/souls")
        assert res.status_code == 200
        assert len(res.json()["souls"]) >= 3

    def test_post_mcp_execute_tool(self):
        payload = {
            "tool_name": "compare_model_benchmarks",
            "arguments": {},
            "soul_id": "cientifico_causal"
        }
        res = client.post("/api/mcp/execute-tool", json=payload)
        assert res.status_code == 200
        assert res.json()["jsonrpc"] == "2.0"
