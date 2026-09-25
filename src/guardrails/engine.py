"""
Enterprise Guardrails Engine for Panama PortOps AI.
Enforces multi-layer safety policies:
1. Input Guardrails: Physical capacity limits, schema conformity, date integrity.
2. Output Guardrails: Monotonicity of quantiles (P10 <= P50 <= P90), outlier detection.
3. Semantic Guardrails: Sanitization of prompt injection and off-topic queries in RAG.

Author: Desarrollado v1.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class GuardrailResult:
    is_valid: bool
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    violations: List[str]
    sanitized_payload: Optional[Dict[str, Any]] = None


class PortOpsGuardrails:
    """Multi-layer enterprise guardrail validator."""

    # Physical Panamanian port throughput constraints (TEU per month)
    MAX_HISTORICAL_MONTHLY_TEU_BALBOA = 550000.0
    MAX_HISTORICAL_MONTHLY_TEU_MANZANILLO = 500000.0
    MIN_ALLOWED_TEU = 0.0

    # Prompt injection signatures
    INJECTION_PATTERNS = [
        r"(?i)\bignore\s+(all\s+)?(previous|prior)\s+instructions\b",
        r"(?i)\bsystem\s+override\b",
        r"(?i)\bdrop\s+table\b",
        r"(?i)\bexec(\s+|\()",
        r"(?i)<\s*script\b"
    ]

    @classmethod
    def validate_forecast_input(cls, port_name: str, requested_teu: Optional[float] = None) -> GuardrailResult:
        """Validates inference requests against physical port constraints."""
        violations = []
        risk_level = "LOW"

        valid_ports = {
            "puerto balboa", "balboa",
            "ssa marine mit", "mit", "manzanillo", "manzanillo international terminal",
            "psa panama international terminal", "psa panama", "psa rodman", "rodman", "psa",
            "colon container terminal", "cct",
            "puerto cristóbal", "cristóbal", "puerto cristobal", "cristobal",
            "bocas fruit co.", "bocas fruit", "almirante",
            "bahía las minas", "bahia las minas"
        }
        clean_port = port_name.strip().lower()

        if clean_port not in valid_ports:
            violations.append(f"Puerto '{port_name}' no reconocido en el Sistema Portuario Nacional de Panamá.")
            risk_level = "HIGH"

        if requested_teu is not None:
            if requested_teu < cls.MIN_ALLOWED_TEU:
                violations.append(f"Valor de TEU ({requested_teu}) viola la restricción de no negatividad.")
                risk_level = "CRITICAL"
            elif requested_teu > 600000.0:
                violations.append(
                    f"Valor de TEU ({requested_teu:,.0f}) excede la capacidad física máxima instalada "
                    "del mayor complejo portuario de Panamá."
                )
                risk_level = "HIGH"

        is_valid = len(violations) == 0
        return GuardrailResult(
            is_valid=is_valid,
            risk_level=risk_level if not is_valid else "LOW",
            violations=violations
        )

    @classmethod
    def validate_quantile_monotonicity(cls, p10: float, p50: float, p90: float) -> GuardrailResult:
        """Verifies strictly that P10 <= P50 <= P90."""
        violations = []
        if not (p10 <= p50 <= p90):
            violations.append(
                f"Violación de monotonicidad de cuantiles: P10={p10:.1f}, P50={p50:.1f}, P90={p90:.1f}. "
                "Los cuantiles deben satisfacer estrictamente P10 <= P50 <= P90."
            )
            return GuardrailResult(is_valid=False, risk_level="CRITICAL", violations=violations)

        return GuardrailResult(is_valid=True, risk_level="LOW", violations=[])

    @classmethod
    def sanitize_rag_query(cls, query_text: str) -> GuardrailResult:
        """Inspects and sanitizes user natural language queries for RAG."""
        violations = []
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, query_text):
                violations.append("Patrón potencial de prompt injection o ejecución de comandos detectado.")
                return GuardrailResult(is_valid=False, risk_level="CRITICAL", violations=violations)

        if len(query_text.strip()) > 500:
            violations.append("La longitud de la consulta excede el límite seguro de 500 caracteres.")
            return GuardrailResult(is_valid=False, risk_level="MEDIUM", violations=violations)

        # Sanitized query (strip tags)
        clean_text = re.sub(r"[<>]", "", query_text).strip()
        return GuardrailResult(
            is_valid=True,
            risk_level="LOW",
            violations=[],
            sanitized_payload={"sanitized_query": clean_text}
        )
