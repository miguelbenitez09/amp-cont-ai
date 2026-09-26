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

    @classmethod
    def validate_maritime_context(cls, query_text: str) -> GuardrailResult:
        """
        Identifies whether query pertains to Panamanian maritime, port, customs, or logistics domain.
        Prevents off-topic diversion, jailbreaks, and unrelated tasks.
        """
        # First sanitize injections
        san_res = cls.sanitize_rag_query(query_text)
        if not san_res.is_valid:
            return san_res

        q_lower = query_text.lower()
        domain_keywords = [
            "puerto", "port", "terminal", "balboa", "cristóbal", "cristobal", "manzanillo", "mit",
            "psa", "rodman", "cct", "bocas fruit", "teu", "contenedor", "container", "bunkering",
            "combustible", "calado", "draft", "canal", "acp", "amp", "fondeadero", "grúa", "sts",
            "patio", "yard", "arancel", "hs code", "dai", "itbms", "aduanas", "ana", "mida",
            "minsa", "apa", "cif", "edifact", "baplie", "coarri", "iso 6346", "ley 6", "ley 56",
            "mlops", "pronóstico", "forecast", "monte carlo", "var", "cvar", "riesgo", "worm"
        ]

        # Check if at least one domain keyword matches or if query contains numbers/codes
        matches = [kw for kw in domain_keywords if kw in q_lower]
        if not matches and len(query_text.split()) > 4:
            # Query is out of domain
            return GuardrailResult(
                is_valid=False,
                risk_level="MEDIUM",
                violations=["Consulta fuera de contexto operativo. El sistema está acotado exclusivamente al ámbito marítimo, portuario, aduanero y logístico de Panamá."],
                sanitized_payload={"matched_keywords": [], "domain_relevant": False}
            )

        return GuardrailResult(
            is_valid=True,
            risk_level="LOW",
            violations=[],
            sanitized_payload={"matched_keywords": matches, "domain_relevant": True}
        )

    @classmethod
    def validate_role_capability(cls, user_roles: List[str], required_capability: str) -> GuardrailResult:
        """
        Verifies if user's roles grant the requested operational capability.
        """
        if not user_roles:
            user_roles = ["readonly_viewer"]

        # Root admin has universal access
        if "root_administrator" in user_roles or "root" in user_roles:
            return GuardrailResult(is_valid=True, risk_level="LOW", violations=[])

        role_permissions_map = {
            "root_administrator": ["*"],
            "maritime_auditor": ["audit.read", "models.read", "data.read", "simulations.read", "worm.verify"],
            "port_operations_director": ["operations.manage", "models.read", "simulations.run", "data.read"],
            "terminal_operator": ["operations.read", "models.read", "containers.validate"],
            "customs_officer": ["customs.read", "customs.calculate", "containers.validate"],
            "lead_data_scientist": ["models.train", "models.evaluate", "models.promote", "features.manage"],
            "readonly_viewer": ["models.read", "data.read", "health.read"]
        }

        user_allowed_caps = set()
        for r in user_roles:
            caps = role_permissions_map.get(r, ["readonly"])
            user_allowed_caps.update(caps)

        if "*" in user_allowed_caps or required_capability in user_allowed_caps:
            return GuardrailResult(is_valid=True, risk_level="LOW", violations=[])

        return GuardrailResult(
            is_valid=False,
            risk_level="HIGH",
            violations=[f"Rol no autorizado: se requiere la capacidad '{required_capability}' para esta operación."],
            sanitized_payload={"user_roles": user_roles, "required_capability": required_capability}
        )

    @classmethod
    def validate_soul_security(cls, soul_id: str) -> GuardrailResult:
        """
        Verifies the cryptographic immutability and anti-tamper seal of an MCP Soul.
        """
        from src.mcp.soul_manager import MCPSoulManager
        verification = MCPSoulManager.verify_soul_seal(soul_id)
        if not verification.get("valid"):
            return GuardrailResult(
                is_valid=False,
                risk_level="CRITICAL",
                violations=[verification.get("reason", "Fallo de validación criptográfica en Soul.")]
            )
        return GuardrailResult(
            is_valid=True,
            risk_level="LOW",
            violations=[],
            sanitized_payload=verification
        )
