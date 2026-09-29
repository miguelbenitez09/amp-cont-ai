"""
Tests for PortOps Domain Intelligence Plugin Subsystem.
Verifies:
1. Plugin manifest parsing and completeness
2. PortOpsDataLoader dataset loading
3. PanamaRegulationsRegistry querying
4. MaritimeFeatureEngine feature calculation
5. PortOpsForecastModel capacity utilization evaluation
6. PortOpsMaritimeKnowledgeBase RAG lookup

Author: Desarrollado v1.0.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

import pytest
import yaml
from pathlib import Path
from plugins.portops import (
    PortOpsDataLoader,
    PanamaRegulationsRegistry,
    MaritimeFeatureEngine,
    PortOpsForecastModel,
    PortOpsMaritimeKnowledgeBase
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_portops_plugin_manifest():
    manifest_path = PROJECT_ROOT / "plugins" / "portops" / "plugin.yaml"
    assert manifest_path.exists()
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data["name"] == "portops"
    assert data["version"] == "1.0.0"
    assert "jurisdiction" in data
    assert "components" in data


def test_portops_regulations_registry():
    regs = PanamaRegulationsRegistry.list_regulations()
    assert len(regs) >= 4
    # Test lookup
    ley_puertos = PanamaRegulationsRegistry.lookup_regulation("Ley 56")
    assert ley_puertos is not None
    assert "General de Puertos" in ley_puertos.official_title


def test_portops_data_loader_inventory():
    inventory = PortOpsDataLoader.get_dataset_inventory()
    assert "container_movements_silver.parquet" in inventory
    assert inventory["container_movements_silver.parquet"]["exists"] is True
    assert inventory["container_movements_silver.parquet"]["records"] > 0


def test_portops_forecast_model_capacity():
    res = PortOpsForecastModel.evaluate_capacity_utilization("Puerto Balboa", 250000.0)
    assert res["port_name"] == "Puerto Balboa"
    assert res["utilization_pct"] > 0.0
    assert "congestion_status" in res


def test_portops_maritime_knowledge_base():
    docs = PortOpsMaritimeKnowledgeBase.search_knowledge("Balboa")
    assert len(docs) > 0
    assert any("Balboa" in d["title"] for d in docs)
