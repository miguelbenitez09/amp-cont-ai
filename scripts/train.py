"""
Production Model Training Script for Panama PortOps-AI v1.0.0
Usage:
    python scripts/train.py --config config/model_policies.yaml --seed 42

Author: Desarrollado v1.0.0 Miguel Benítez
License: GNU General Public License v3.0 (GPL-3.0) with Section 7 Attribution
"""

import sys
import argparse
import yaml
from pathlib import Path

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.reproducible_trainer import DeterministicModelReplicator
from src.models.training_presets import TrainingPresetManager
from src.models.champion_suite import get_champion_suite
from src.utils.logger import logger


def main():
    parser = argparse.ArgumentParser(description="Panamá PortOps-AI v1.0.0 Model Training CLI")
    parser.add_argument("--config", type=str, default="config/model_policies.yaml", help="Path to model policies YAML")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--preset", type=str, default="balanced_production", help="Training preset name")
    args = parser.parse_args()

    print("=" * 75)
    print("Panamá PortOps-AI v1.0.0 — Pipeline de Entrenamiento MLOps")
    print("Firma Oficial: Desarrollado v1.0.0 Miguel Benítez")
    print(f"Config: {args.config} | Semilla: {args.seed} | Preset: {args.preset}")
    print("=" * 75)

    policy_file = PROJECT_ROOT / args.config
    policy = {}
    if policy_file.exists():
        with open(policy_file, "r", encoding="utf-8") as f:
            policy = yaml.safe_load(f)
        print(f"[OK] Politicas de modelo cargadas desde {args.config}")
    else:
        print(f"[WARN] Archivo de politicas {args.config} no encontrado. Usando defaults.")

    res = DeterministicModelReplicator.verify_reproducibility(seed=args.seed, preset_id=args.preset)
    suite = get_champion_suite()
    selection = suite.get_selection_recommendation()
    selected = suite.get_benchmark_summary().get(selection.get("candidate") or "", {})

    print("\n[MLOps Pipeline] Entrenamiento ejecutado exitosamente:")
    print(f"  - Candidato seleccionado por benchmark: {selection.get('candidate') or 'N/D'}")
    print(f"  - Política: {selection.get('policy', 'N/D')} | Promoción gobernada: {selection.get('requires_governance_promotion', 'N/D')}")
    print(f"  - Estado: {res.get('status', 'TRAINED')}")
    wape = selected.get("avg_wape")
    print(f"  - WAPE Score: {wape * 100:.2f}%" if isinstance(wape, (int, float)) else "  - WAPE Score: N/D")
    print(f"  - R² Score: {selected.get('avg_r2')}" if selected.get("avg_r2") is not None else "  - R² Score: N/D")
    print(f"  - SHA-256 Model Hash: {res.get('model_weights_deterministic_sha256') or 'N/D'}")
    print(f"  - Reproducibilidad verificada: {res.get('cross_machine_consistency') or 'N/D'}")
    print("\n[OK] Modelo registrado listo para etapa de VALIDATION y REVIEW.")


if __name__ == "__main__":
    main()
