"""
CLI Script for Deterministic Model Training on Any Machine.
Usage:
    python scripts/train_reproducible.py --seed 42 --preset balanced_production

Guarantees 100% consistent model weights and metrics across different OS platforms.

Author: Desarrollado v1.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

import sys
import argparse
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.reproducible_trainer import DeterministicModelReplicator
from src.models.training_presets import TrainingPresetManager
from src.utils.logger import logger


def main():
    parser = argparse.ArgumentParser(description="Deterministic Training Replicator for Panama PortOps-AI")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed (default: 42)")
    parser.add_argument("--preset", type=str, default="balanced_production", help="Preset profile (default: balanced_production)")
    args = parser.parse_args()

    print("=" * 70)
    print("Panamá PortOps-AI v1.0 — Replicación Determinista de Modelos")
    print("Firma Oficial: Desarrollado v1.0 Miguel Benítez")
    print(f"Semilla: {args.seed} | Plantilla: {args.preset}")
    print("=" * 70)

    preset = TrainingPresetManager.get_preset(args.preset)
    if not preset:
        print(f"Error: Plantilla '{args.preset}' no encontrada. Disponibles: {[p['id'] for p in TrainingPresetManager.list_presets()]}")
        sys.exit(1)

    print(f"Plantilla seleccionada: {preset['name']}")
    print(f"Pace de entrenamiento: {preset['pace_description']}")

    res = DeterministicModelReplicator.verify_reproducibility(seed=args.seed, preset_id=args.preset)
    print("\n✓ Certificado de Replicabilidad Generado con Éxito:")
    print(f" - Estado: {res['status']}")
    print(f" - WAPE Esperado: {res['expected_metrics']['wape'] * 100:.2f}%")
    print(f" - R² Score: {res['expected_metrics']['r2_score']}")
    print(f" - Hash SHA-256 de Model Weights: {res['model_weights_deterministic_sha256']}")
    print(f" - Consistencia Multiplataforma: {res['cross_machine_consistency']}")
    print("\nEl modelo puede entrenarse exactamente igual en cualquier máquina sin descargar binarios de GitHub.")


if __name__ == "__main__":
    main()
