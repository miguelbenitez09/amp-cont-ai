"""
Pruebas automatizadas de integración y resiliencia para el Supervisor Autónomo
de Comercio Exterior (INEC).
Autor: Desarrollado v1.0.0 Miguel Benítez / Ing. Miguel Antonio Benítez González (UTP) - GNU GPL-3.0
"""
import json
import pytest
from pathlib import Path
from tools.scrapers.comext_autonomous_supervisor import ComextSupervisor, STATE_FILE


def test_supervisor_initialization_and_state():
    """Valida inicialización y persistencia de estado del supervisor."""
    supervisor = ComextSupervisor(batch_size=2)
    assert supervisor.batch_size == 2
    assert "started_at" in supervisor.state
    assert "total_cycles_executed" in supervisor.state


def test_supervisor_scan_pending_tasks():
    """Valida que el escaneo de tareas detecte capítulos pendientes o informe cola vacía."""
    supervisor = ComextSupervisor(batch_size=1)
    queue = supervisor.scan_pending_tasks()
    assert isinstance(queue, list)
    for task in queue:
        assert "target" in task
        assert "report_id" in task
        assert "capitulo" in task
        assert task["target"] in ["imports", "exports"]
        assert task["report_id"] in [3, 4]


def test_supervisor_state_persistence(tmp_path):
    """Verifica guardado y recarga de estado sin corrupción de datos."""
    supervisor = ComextSupervisor()
    supervisor.state["total_cycles_executed"] += 1
    supervisor.save_state()

    assert STATE_FILE.exists()
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_cycles_executed"] >= 1
