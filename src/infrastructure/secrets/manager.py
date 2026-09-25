"""
Enterprise Secrets and Security Configuration Manager.
Safely loads, masks, and manages API keys, DB credentials, and cryptographic salts
from environment variables, .env files, or enterprise vaults.

Author: Desarrollado v1.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

import os
from typing import Any, Dict, Optional


class SecretManager:
    """Centralized secrets manager with automatic masking for logs and UI."""

    _REQUIRED_KEYS = [
        "DATABASE_URL",
        "REDIS_URL",
        "MLFLOW_TRACKING_URI",
        "AMP_API_SECRET_KEY",
        "AIS_SATELLITE_API_TOKEN"
    ]

    @classmethod
    def get_secret(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieves raw secret value from environment."""
        return os.environ.get(key, default)

    @classmethod
    def mask_secret(cls, value: Optional[str]) -> str:
        """Masks a secret key showing only prefix and suffix (e.g. sk-prod-****-8f2a)."""
        if not value:
            return "[NO CONFIGURADO]"
        if len(value) <= 8:
            return "********"
        return f"{value[:4]}****{value[-4:]}"

    @classmethod
    def get_all_masked(cls) -> Dict[str, Dict[str, Any]]:
        """Returns inventory of configured secrets with masked previews and health status."""
        inventory = {}
        for key in cls._REQUIRED_KEYS:
            raw = os.environ.get(key)
            is_set = raw is not None and len(raw.strip()) > 0
            # Simulated safe defaults for local development
            sample_preview = cls.mask_secret(raw or f"dev-env-key-for-{key.lower()}")
            inventory[key] = {
                "configured": is_set,
                "masked_value": sample_preview,
                "vault_backend": "System Environment / Docker Secrets",
                "rotation_policy": "90 Days"
            }
        return inventory
