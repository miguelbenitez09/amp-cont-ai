"""
Test Suite for Agentic Swarm, MCP Tools, Inference Engine, Customs & ISO 6346 Modules
Panama PortOps-AI v2.0
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import pytest
import requests
from src.data.parsers.container_iso6346 import (
    ISO6346ContainerValidator,
    EDIFACTMaritimeParser,
)
from src.data.scrapers.ana_hscode_scraper import PanamaTariffDatabase
from src.models.inference.engine import OptimizedInferenceEngine
from src.infrastructure.llm_client import UnifiedLLMClient
from src.agents.swarm import MaritimeAgentSwarm, get_agent_swarm
from src.mcp.tools import get_available_tools_schema, execute_tool

BASE_URL = "http://127.0.0.1:8000"


# ---------------------------------------------------------
# 1. ISO 6346 & EDIFACT Tests
# ---------------------------------------------------------

def test_container_iso6346_valid():
    # MSKU1234565 has check digit 5
    result = ISO6346ContainerValidator.validate_container_id("MSKU1234565")
    assert result["valid"] is True
    assert result["owner_code"] == "MSK"
    assert result["category_identifier"] == "U"
    assert "Freight Container" in result["category_description"]
    assert result["serial_number"] == "123456"
    assert result["check_digit_actual"] == 5
    assert result["check_digit_expected"] == 5


def test_container_iso6346_invalid_check_digit():
    result = ISO6346ContainerValidator.validate_container_id("MSKU1234569")
    assert result["valid"] is False
    assert result["check_digit_actual"] == 9
    assert result["check_digit_expected"] == 5
    assert "mismatch" in result["reason"].lower()


def test_container_manifest_entry():
    res = ISO6346ContainerValidator.parse_full_manifest_entry("MSKU1234565", size_type="45R1")
    assert res["validation"]["valid"] is True
    assert res["equipment_spec"]["is_reefer"] is True
    assert res["teus"] == 2.0


def test_parse_edifact_coarri():
    raw_coarri = """
    UNB+UNOA:2+MAEU+PANAMA+260926:1200+1'
    UNH+1+COARRI:D:95B:UN:SMDG20'
    BGM+EX1+VESSEL001+9'
    TDT+20+2409W+1++MSK+++MSC PAMELA'
    LOC+147+PA-BAL'
    EQD+CN+MSKU1234565:45R1:102:5++2+5'
    MEA+WT++KGM:24500'
    UNT+7+1'
    UNZ+1+1'
    """
    summary = EDIFACTMaritimeParser.parse_coarri_summary(raw_coarri)
    assert summary["message_type"] == "COARRI"
    assert summary["vessel_identified"] == "MSC PAMELA"
    assert summary["total_containers_reported"] == 1
    assert "MSKU1234565" in summary["container_list"]


# ---------------------------------------------------------
# 2. Customs HS-Code & Landed Cost Tests
# ---------------------------------------------------------

def test_customs_tariff_search():
    results = PanamaTariffDatabase.search_by_text("carne")
    assert len(results) >= 1
    match = results[0]
    assert "0201" in match["hs_code_panama"]
    assert match["arancel_dai_pct"] >= 0.0


def test_customs_tariff_search_code():
    match = PanamaTariffDatabase.lookup_by_hs_code("870323")
    assert match is not None
    assert "automóviles" in match["descripcion"].lower()


def test_customs_landed_cost_calculation():
    # CIF $10,000 for meat (DAI 25%, ITBMS 0% exempt food)
    cost = PanamaTariffDatabase.calculate_landed_customs_cost("0201.30.00.00.20", cif_value_usd=10000.0)
    assert cost["cif_value_usd"] == 10000.0
    assert cost["dai_rate_pct"] == 25.0
    assert cost["dai_usd"] == 2500.0
    assert cost["itbms_usd"] == 0.0   # Food exempt
    assert cost["customs_declaration_fee_usd"] == 70.0
    assert cost["total_import_taxes_usd"] == 2570.0
    assert cost["total_landed_cost_usd"] == 12570.0


# ---------------------------------------------------------
# 3. Inference Engine & Sub-millisecond Guarantees
# ---------------------------------------------------------

def test_inference_engine_quantile_anticrossing():
    engine = OptimizedInferenceEngine()
    pred = engine.predict_terminal(port="Puerto Balboa", horizon_months=1)
    q = pred["forecast_quantiles_teus"]
    assert q["p10_pessimistic_floor"] <= q["p50_median_central"] <= q["p90_capacity_stress"]
    assert q["p10_pessimistic_floor"] > 0.0
    assert pred["anti_crossing_verified"] is True
    assert pred["latency_ms"] < 50.0  # Vectorized in-memory forecast


def test_inference_engine_all_ports():
    engine = OptimizedInferenceEngine()
    for port in ["Puerto Balboa", "Puerto Cristóbal", "SSA Marine MIT", "PSA Panama International Terminal"]:
        pred = engine.predict_terminal(port=port, horizon_months=3)
        q = pred["forecast_quantiles_teus"]
        assert q["p10_pessimistic_floor"] <= q["p50_median_central"] <= q["p90_capacity_stress"]
        assert pred["port"] == port


# ---------------------------------------------------------
# 4. LLM Multi-Runtime Client Tests
# ---------------------------------------------------------

def test_llm_client_resilience():
    client = UnifiedLLMClient()
    resp = client.generate_chat_response(
        system_prompt="Contexto marítimo industrial",
        user_message="Analizar el riesgo de congestión en el muelle de Balboa",
    )
    assert "content" in resp
    assert len(resp["content"]) > 20
    assert resp["backend_used"] in ["vLLM (PagedAttention)", "Ollama (Quantized)", "Maritime Domain Expert Engine (Deterministic Fallback)"]


# ---------------------------------------------------------
# 5. Maritime Swarm & MCP Tools Tests
# ---------------------------------------------------------

def test_agent_swarm_routing():
    swarm = get_agent_swarm()
    agents = swarm.list_available_agents()
    assert len(agents) == 4
    agent_ids = [a["agent_id"] for a in agents]
    assert "agent_aduanero_tariff" in agent_ids
    assert "agent_auditor_maritimo" in agent_ids
    assert "agent_operador_muelle" in agent_ids
    assert "agent_causal_risk" in agent_ids


def test_agent_swarm_chat_execution():
    swarm = get_agent_swarm()
    res = swarm.process_message(
        query="Cuál es el arancel DAI y permisos aduaneros para importar vehículos a Panamá?",
    )
    assert res["agent_id"] == "agent_aduanero_tariff"
    assert len(res["response"]) > 0
    assert "routing" in res
    assert res["routing"]["latency_ms"] >= 0.0


def test_mcp_tools_list_and_schema():
    tools = get_available_tools_schema()
    assert len(tools) >= 5
    tool_names = [t["name"] for t in tools]
    assert "lookup_panama_customs_tariff" in tool_names
    assert "validate_iso6346_container" in tool_names
    assert "get_port_forecast" in tool_names


def test_mcp_tool_execution():
    # Execute ISO 6346 tool
    res = execute_tool("validate_iso6346_container", {"container_id": "MSKU1234565", "size_type": "45G1"})
    assert res["validation"]["valid"] is True
    assert res["container_id"] == "MSKU1234565"

    # Execute Tariff tool
    res_t = execute_tool("lookup_panama_customs_tariff", {"hs_code": "020130", "cif_value_usd": 15000.0})
    assert res_t["cif_value_usd"] == 15000.0
    assert res_t["total_landed_cost_usd"] > 15000.0


# ---------------------------------------------------------
# 6. REST API Endpoints Integration Tests
# ---------------------------------------------------------

def test_api_agents_list():
    res = requests.get(f"{BASE_URL}/api/v1/agents/list", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert len(data["agents"]) == 4


def test_api_agents_chat():
    payload = {
        "query": "Cuál es el riesgo de congestión para Balboa en las próximas 48 horas?",
        "context": {}
    }
    res = requests.post(f"{BASE_URL}/api/v1/agents/chat", json=payload, timeout=10)
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert "agent_id" in data
    assert data["agent_id"] in ["agent_causal_risk", "agent_auditor_maritimo", "agent_operador_muelle"]


def test_api_mcp_tools():
    res = requests.get(f"{BASE_URL}/api/v1/mcp/tools", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert "Model Context Protocol" in data["protocol"]
    assert len(data["tools"]) >= 5


def test_api_mcp_execute():
    payload = {
        "tool_name": "validate_iso6346_container",
        "arguments": {"container_id": "MSKU1234565", "size_type": "45G1"}
    }
    res = requests.post(f"{BASE_URL}/api/v1/mcp/execute", json=payload, timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["result"]["validation"]["valid"] is True


def test_api_customs_tariff_search():
    res = requests.get(f"{BASE_URL}/api/v1/customs/tariff/search?query=carne", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["total_matches"] >= 1
    assert data["items"][0]["arancel_dai_pct"] >= 0.0


def test_api_customs_tariff_calculate():
    payload = {"hs_code": "0201.30.00.00.20", "cif_value_usd": 20000.0}
    res = requests.post(f"{BASE_URL}/api/v1/customs/tariff/calculate", json=payload, timeout=5)
    assert res.status_code == 200
    data = res.json()
    liq = data["liquidation"]
    assert liq["dai_usd"] == 5000.0
    assert liq["total_landed_cost_usd"] == 25070.0


def test_api_container_validate():
    payload = {"container_id": "MSKU1234565", "size_type": "22G1"}
    res = requests.post(f"{BASE_URL}/api/v1/containers/validate", json=payload, timeout=5)
    assert res.status_code == 200
    data = res.json()
    record = data["result"]
    assert record["validation"]["valid"] is True
    assert record["validation"]["owner_code"] == "MSK"
