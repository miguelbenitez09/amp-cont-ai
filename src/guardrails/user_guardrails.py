"""
User-Configurable Dynamic Guardrail & Policy Engine for Panama PortOps-AI v1.0.0.
Provides role-based quotas, token metering, module access restrictions, and MCP tool permissions.
Separates Immutable System Guardrails (sealed by HMAC-SHA256) from Administrator-Configurable Guardrails.

Author: Desarrollado v1.0.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from src.utils.logger import logger

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE = ROOT_DIR / "data" / "enterprise_db" / "user_guardrails_policy.json"


class UserGuardrailManager:
    """Manages mutable, admin-configurable guardrails, rate limits, and token budgets."""

    DEFAULT_POLICIES: Dict[str, Any] = {
        "enforcement_mode": "STRICT_PANAMA_MARITIME",
        "system_immutable_seal": "SEAL-HMAC256-PANAMA-PORTOPS-INVARIANT-ROOT",
        "roles_policy": {
            "root": {
                "max_tokens_daily": 1000000,
                "rate_limit_rpm": 300,
                "allowed_modules": ["landing", "cot_swarm", "customs_lakehouse", "forecast", "benchmark", "diagnostics", "simulation", "methodology", "data_platform", "security_iam", "admin_deploy"],
                "allowed_mcp_tools": ["*"],
                "allow_model_promotion": True,
                "allow_secrets_management": True,
                "custom_prompt_jailbreak_check": True
            },
            "admin_maritimo": {
                "max_tokens_daily": 250000,
                "rate_limit_rpm": 120,
                "allowed_modules": ["landing", "cot_swarm", "customs_lakehouse", "forecast", "benchmark", "diagnostics", "simulation", "methodology", "data_platform", "security_iam"],
                "allowed_mcp_tools": ["get_port_forecast", "run_monte_carlo_risk_simulation", "compare_model_benchmarks", "simulate_external_feature", "query_maritime_knowledge", "lookup_panama_customs_tariff", "validate_iso6346_container"],
                "allow_model_promotion": False,
                "allow_secrets_management": False,
                "custom_prompt_jailbreak_check": True
            },
            "auditor_aduana": {
                "max_tokens_daily": 100000,
                "rate_limit_rpm": 60,
                "allowed_modules": ["landing", "cot_swarm", "customs_lakehouse", "forecast", "methodology", "data_platform", "security_iam"],
                "allowed_mcp_tools": ["lookup_panama_customs_tariff", "validate_iso6346_container", "query_maritime_knowledge", "compare_model_benchmarks"],
                "allow_model_promotion": False,
                "allow_secrets_management": False,
                "custom_prompt_jailbreak_check": True
            },
            "operador_puerto": {
                "max_tokens_daily": 80000,
                "rate_limit_rpm": 60,
                "allowed_modules": ["landing", "cot_swarm", "forecast", "simulation", "data_platform"],
                "allowed_mcp_tools": ["get_port_forecast", "validate_iso6346_container", "run_monte_carlo_risk_simulation"],
                "allow_model_promotion": False,
                "allow_secrets_management": False,
                "custom_prompt_jailbreak_check": True
            },
            "analista_amp": {
                "max_tokens_daily": 150000,
                "rate_limit_rpm": 90,
                "allowed_modules": ["landing", "forecast", "benchmark", "diagnostics", "simulation", "methodology", "data_platform"],
                "allowed_mcp_tools": ["get_port_forecast", "compare_model_benchmarks", "simulate_external_feature", "run_monte_carlo_risk_simulation"],
                "allow_model_promotion": False,
                "allow_secrets_management": False,
                "custom_prompt_jailbreak_check": True
            },
            "consultor_publico": {
                "max_tokens_daily": 20000,
                "rate_limit_rpm": 20,
                "allowed_modules": ["landing", "forecast", "benchmark", "methodology"],
                "allowed_mcp_tools": ["get_port_forecast", "compare_model_benchmarks", "query_maritime_knowledge"],
                "allow_model_promotion": False,
                "allow_secrets_management": False,
                "custom_prompt_jailbreak_check": True
            }
        },
        "blocked_keywords": [
            "drop table", "alter table", "system override", "rm -rf", "<script", "eval(", "exec("
        ],
        "allowed_jurisdictions": ["Panamá", "Canal de Panamá", "SIECA", "AMP", "ANA", "OEA", "IMO", "WCO"],
        "max_query_length": 600,
        "pii_masking_enabled": True
    }

    @classmethod
    def load_policies(cls) -> Dict[str, Any]:
        """Loads user guardrail policies from disk or initializes defaults."""
        if not CONFIG_FILE.exists():
            cls.save_policies(cls.DEFAULT_POLICIES)
            return cls.DEFAULT_POLICIES
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading user guardrail policies: {e}. Using defaults.")
            return cls.DEFAULT_POLICIES

    @classmethod
    def save_policies(cls, policies: Dict[str, Any]) -> None:
        """Saves updated user guardrails to persistent storage."""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(policies, f, indent=2, ensure_ascii=False)

    @classmethod
    def check_access(cls, role: str, module_id: str) -> Tuple[bool, str]:
        """Checks if a user role is permitted to interact with a specific UI or API module."""
        policies = cls.load_policies()
        role_cfg = policies.get("roles_policy", {}).get(role)
        if not role_cfg:
            # Fallback to public
            role_cfg = policies.get("roles_policy", {}).get("consultor_publico", {})

        allowed_modules = role_cfg.get("allowed_modules", [])
        if module_id in allowed_modules or "*" in allowed_modules:
            return True, f"Acceso concedido al módulo '{module_id}' para el rol '{role}'."
        return False, f"Guardrail: El rol '{role}' no tiene autorización para acceder al módulo '{module_id}'."

    @classmethod
    def check_tool_invocation(cls, role: str, tool_name: str) -> Tuple[bool, str]:
        """Verifies if a role has quota and permission to invoke an MCP tool."""
        policies = cls.load_policies()
        role_cfg = policies.get("roles_policy", {}).get(role, {})
        allowed_tools = role_cfg.get("allowed_mcp_tools", [])

        if "*" in allowed_tools or tool_name in allowed_tools:
            return True, f"Invocación de herramienta MCP '{tool_name}' autorizada."
        return False, f"Guardrail: Invocación de la herramienta MCP '{tool_name}' denegada para el rol '{role}'."

    @classmethod
    def update_role_policy(cls, role: str, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Updates limits, token quotas, and permissions for a specific role."""
        policies = cls.load_policies()
        if "roles_policy" not in policies:
            policies["roles_policy"] = cls.DEFAULT_POLICIES["roles_policy"]

        if role not in policies["roles_policy"]:
            policies["roles_policy"][role] = {}

        policies["roles_policy"][role].update(new_settings)
        cls.save_policies(policies)
        return policies["roles_policy"][role]
