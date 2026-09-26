"""
Feature Registry and Formal Definitions for Panama PortOps-AI v2.0
Defines feature schemas, leakage safety declarations, and mathematical transformations.
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

from typing import Dict, Any, List
from pydantic import BaseModel


class FeatureDefinition(BaseModel):
    name: str
    entity: str
    dtype: str
    source_layer: str
    transformation: str
    parameters: Dict[str, Any]
    leakage_safe: bool = True
    owner: str = "MLOps Team"
    description: str


FEATURE_CATALOG: List[FeatureDefinition] = [
    FeatureDefinition(
        name="teu_lag_1",
        entity="port",
        dtype="float64",
        source_layer="silver",
        transformation="shift",
        parameters={"periods": 1},
        description="Volumen observado en el mes inmediatamente anterior (t-1)."
    ),
    FeatureDefinition(
        name="teu_lag_12",
        entity="port",
        dtype="float64",
        source_layer="silver",
        transformation="shift",
        parameters={"periods": 12},
        description="Memoria estacional interanual del mismo mes del año previo (t-12)."
    ),
    FeatureDefinition(
        name="rolling_mean_3",
        entity="port",
        dtype="float64",
        source_layer="silver",
        transformation="shift_rolling_mean",
        parameters={"window": 3, "shift": 1},
        description="Media móvil trimestral rezagada un período para evitar lookahead bias."
    ),
    FeatureDefinition(
        name="rolling_std_6",
        entity="port",
        dtype="float64",
        source_layer="silver",
        transformation="shift_rolling_std",
        parameters={"window": 6, "shift": 1},
        description="Desviación estándar móvil semestral como indicador de régimen de volatilidad."
    ),
    FeatureDefinition(
        name="yoy_change_pct",
        entity="port",
        dtype="float64",
        source_layer="silver",
        transformation="pct_change_12",
        parameters={"periods": 12},
        description="Tasa de variación interanual respecto al volumen de hace 12 meses."
    ),
    FeatureDefinition(
        name="month_sin",
        entity="calendar",
        dtype="float64",
        source_layer="silver",
        transformation="fourier_harmonic_sin",
        parameters={"period": 12},
        description="Armónico trigonométrico senoidal para codificación cíclica continua."
    ),
    FeatureDefinition(
        name="month_cos",
        entity="calendar",
        dtype="float64",
        source_layer="silver",
        transformation="fourier_harmonic_cos",
        parameters={"period": 12},
        description="Armónico trigonométrico cosenoidal complementario en el círculo unitario."
    ),
    FeatureDefinition(
        name="empty_ratio_lag_1",
        entity="port",
        dtype="float64",
        source_layer="silver",
        transformation="ratio_shift",
        parameters={"numerator": "empty_teu", "denominator": "teu_total", "shift": 1},
        description="Proporción de contenedores vacíos frente al total de carga en t-1."
    )
]


def get_feature_catalog() -> List[Dict[str, Any]]:
    """Returns the serialized feature catalog."""
    return [f.model_dump() for f in FEATURE_CATALOG]
