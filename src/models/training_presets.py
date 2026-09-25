"""
Training Presets and Hyperparameter Profile Manager for Panama PortOps-AI.
Provides structured templates that alter the training pace, regularization,
and learning behavior of LightGBM, Random Forest, and Quantile Regressors.

Author: Desarrollado v1.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional


@dataclass
class TrainingPresetProfile:
    id: str
    name: str
    badge: str
    target_objective: str
    pace_description: str
    recommended_use_case: str
    hyperparameters: Dict[str, Any]
    tradeoffs: Dict[str, str]


class TrainingPresetManager:
    """
    Curated set of 4 industrial training presets designed to adapt model behavior:
    1. Balanced Production (Default Champion)
    2. Conservative / Anti-Overfitting (Slow pace, high regularization)
    3. Aggressive / Rapid Shock Reaction (Fast pace, responsive to disruptions)
    4. Resilient Quantile Stress (High emphasis on P10/P90 tail risk)
    """

    PRESETS: List[TrainingPresetProfile] = [
        TrainingPresetProfile(
            id="balanced_production",
            name="Balanceado Producción (Champion Default)",
            badge="🏆 Estándar MLOps",
            target_objective="WAPE Óptimo (9.11%) y Máxima Capacidad Explicativa (R² 0.9594)",
            pace_description="Ritmo de aprendizaje moderado (learning_rate = 0.05) con 120 iteraciones boosting.",
            recommended_use_case="Operación continua diaria y proyecciones presupuestarias anuales de la AMP.",
            hyperparameters={
                "learning_rate": 0.05,
                "n_estimators": 120,
                "max_depth": 6,
                "num_leaves": 31,
                "min_child_samples": 20,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "reg_alpha": 0.1,
                "reg_lambda": 0.5,
                "deterministic": True,
                "seed": 42
            },
            tradeoffs={
                "ventaja": "Mínimo error ponderado global y convergencia estable.",
                "desventaja": "Reacciona con cierto retardo ante shocks súbitos no anticipados por los rezagos."
            }
        ),
        TrainingPresetProfile(
            id="conservative_anti_overfitting",
            name="Conservador / Anti-Sobreajuste (Pace Pausado)",
            badge="🛡️ Prudencia Operativa",
            target_objective="Generalización Máxima y Regularización Fuerte L2",
            pace_description="Pace pausado (learning_rate = 0.02) con 250 iteraciones y poda estricta de ramas.",
            recommended_use_case="Planificación de concesiones portuarias a 5 años y auditorías de la Contraloría.",
            hyperparameters={
                "learning_rate": 0.02,
                "n_estimators": 250,
                "max_depth": 4,
                "num_leaves": 15,
                "min_child_samples": 35,
                "subsample": 0.7,
                "colsample_bytree": 0.7,
                "reg_alpha": 1.5,
                "reg_lambda": 3.0,
                "deterministic": True,
                "seed": 42
            },
            tradeoffs={
                "ventaja": "Inmune a fluctuaciones anómalas de corto plazo y variabilidad de un solo mes.",
                "desventaja": "Subestima ligeramente los picos estacionales extremos de Fiestas Patrias (noviembre)."
            }
        ),
        TrainingPresetProfile(
            id="aggressive_shock_reaction",
            name="Agresivo / Reacción Rápida a Shocks",
            badge="⚡ Alta Sensibilidad",
            target_objective="Adaptación Inmediata a Disrupciones Recientes (Huelgas / Sequías)",
            pace_description="Pace acelerado (learning_rate = 0.12) con 80 árboles profundos de rápida respuesta.",
            recommended_use_case="Gestión de crisis portuarias durante sequías severas del Canal o huelgas de transporte.",
            hyperparameters={
                "learning_rate": 0.12,
                "n_estimators": 80,
                "max_depth": 8,
                "num_leaves": 63,
                "min_child_samples": 10,
                "subsample": 0.9,
                "colsample_bytree": 0.9,
                "reg_alpha": 0.01,
                "reg_lambda": 0.05,
                "deterministic": True,
                "seed": 42
            },
            tradeoffs={
                "ventaja": "Detecta instantáneamente caídas de volumen por cierres de carreteras.",
                "desventaja": "Mayor volatilidad de predicción en meses de calma."
            }
        ),
        TrainingPresetProfile(
            id="resilient_quantile_stress",
            name="Resiliente Cuantílico de Estrés (P10 / P90)",
            badge="📊 Colas de Riesgo",
            target_objective="Dimensionamiento Robusto de Patios y Grúas STS en Escenarios Críticos",
            pace_description="Pérdida Pinball asimétrica ponderada con penalización incrementada en cuantiles extremos.",
            recommended_use_case="Asignación de cuadrillas de estibadores y reserva de espacios en fondeadero.",
            hyperparameters={
                "learning_rate": 0.04,
                "n_estimators": 180,
                "max_depth": 6,
                "num_leaves": 28,
                "min_child_samples": 18,
                "quantile_alpha_p10": 0.10,
                "quantile_alpha_p90": 0.90,
                "reg_alpha": 0.3,
                "reg_lambda": 1.0,
                "deterministic": True,
                "seed": 42
            },
            tradeoffs={
                "ventaja": "Bandas de incertidumbre operacionales ultra-precisas para prevención de colapso.",
                "desventaja": "El cálculo de medianas puede ser ligeramente más conservador."
            }
        )
    ]

    @classmethod
    def list_presets(cls) -> List[Dict[str, Any]]:
        """Returns the list of all available presets."""
        return [asdict(p) for p in cls.PRESETS]

    @classmethod
    def get_preset(cls, preset_id: str) -> Optional[Dict[str, Any]]:
        """Finds a specific preset by ID."""
        for p in cls.PRESETS:
            if p.id == preset_id:
                return asdict(p)
        return None
