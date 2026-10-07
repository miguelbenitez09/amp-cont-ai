"""
Project Brain Service and Governance Engine.
Loads, manages and validates project source of truth, capabilities, and gap registers.

Author: Ing. Miguel Antonio Benítez González (UTP)
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml


class ProjectBrainService:
    """Service to access and reconcile the sovereign Project Brain repository."""

    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[2]))
        self.brain_dir = self.root_dir / "project_brain"

    def _read_yaml(self, filename: str) -> Dict[str, Any]:
        filepath = self.brain_dir / filename
        if not filepath.exists():
            return {}
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            return {"error": f"Failed to load {filename}: {str(e)}"}

    def get_source_of_truth(self) -> Dict[str, Any]:
        """Returns the active System Source of Truth."""
        return self._read_yaml("SYSTEM_SOURCE_OF_TRUTH.yaml")

    def get_gap_register(self) -> Dict[str, Any]:
        """Returns the registered technical gaps and their current resolution status."""
        return self._read_yaml("GAP_REGISTER.yaml")

    def get_capability_matrix(self) -> Dict[str, Any]:
        """Returns the RBAC capability matrix across all defined roles."""
        return self._read_yaml("CAPABILITY_MATRIX.yaml")

    def get_data_catalog(self) -> Dict[str, Any]:
        """Returns the Medallion Data Catalog."""
        return self._read_yaml("DATA_CATALOG.yaml")

    def get_model_catalog(self) -> Dict[str, Any]:
        """Returns the Machine Learning & RAG Model Catalog."""
        return self._read_yaml("MODEL_CATALOG.yaml")

    def get_security_baseline(self) -> Dict[str, Any]:
        """Returns the Cryptographic & Security Baseline."""
        return self._read_yaml("SECURITY_BASELINE.yaml")

    def evaluate_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a design or architecture alternative using the 5-criterion matrix:
        1. Correctness & Precision (weight: 0.25)
        2. Security & Compliance (weight: 0.20)
        3. Operational Robustness & Maintainability (weight: 0.20)
        4. Performance & Scalability (weight: 0.20)
        5. Developer Experience & Testability (weight: 0.15)

        Eliminatory conditions:
        - Any score < 3.0 in Security or Correctness triggers automatic REJECT.
        """
        weights = {
            "correctness": 0.25,
            "security": 0.20,
            "robustness": 0.20,
            "performance": 0.20,
            "dx": 0.15
        }
        scores = proposal.get("scores", {})
        
        # Check eliminatory conditions
        if scores.get("security", 0) < 3.0:
            return {
                "decision": "REJECTED",
                "reason": "Eliminatory condition triggered: Security score is below 3.0 threshold.",
                "total_score": 0.0
            }
        if scores.get("correctness", 0) < 3.0:
            return {
                "decision": "REJECTED",
                "reason": "Eliminatory condition triggered: Correctness score is below 3.0 threshold.",
                "total_score": 0.0
            }

        total_score = sum(scores.get(dim, 0) * weight for dim, weight in weights.items())
        decision = "APPROVED" if total_score >= 3.8 else "NEEDS_REVISION"

        return {
            "decision": decision,
            "total_score": round(total_score, 2),
            "breakdown": scores,
            "weights": weights
        }


# Singleton brain instance
brain_service = ProjectBrainService()
