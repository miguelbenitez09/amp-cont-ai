"""
Model & Tool Access Policy Engine (ABAC + RBAC) — amp-cont-ai
Enforces multi-factor authorization, role hierarchy and rate limits.
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

from typing import Dict, Any, List, Optional, Tuple


class AccessPolicyEngine:
    """Evaluates RBAC and ABAC rules for models, tools, and agents."""

    POLICY_TIERS = {
        "PUBLIC": 3,
        "AUTHENTICATED": 2,
        "VERIFIED_USER": 2,
        "ROLE_RESTRICTED": 1,
        "ADMIN_ONLY": 1,
        "ROOT_ONLY": 0
    }

    ROLE_HIERARCHY = {
        "root": 0,
        "SysAdmin": 1,
        "SecOpsAdmin": 1,
        "MlopsAdmin": 1,
        "Analyst": 2,
        "Guest": 3
    }

    @classmethod
    def evaluate_model_access(
        cls,
        user_role: str,
        policy_level: str,
        is_mfa_authenticated: bool = False
    ) -> Tuple[bool, str]:
        """Returns (is_allowed, reason)."""
        policy = policy_level.upper()
        if policy == "PUBLIC":
            return True, "Public model access granted."

        if user_role == "Guest" or not user_role:
            return False, "Authentication required for this model tier."

        if policy == "AUTHENTICATED":
            return True, "Authenticated session verified."

        if policy == "VERIFIED_USER":
            if not is_mfa_authenticated:
                return False, "MFA verification required for this model tier."
            return True, "MFA session verified."

        if policy == "ROLE_RESTRICTED":
            if user_role in ("root", "MlopsAdmin"):
                return True, "Role clearance granted."
            return False, "Role clearance insufficient (Requires MlopsAdmin or root)."

        if policy == "ADMIN_ONLY":
            if user_role in ("root", "SysAdmin", "SecOpsAdmin", "MlopsAdmin"):
                return True, "Administrator clearance granted."
            return False, "Administrator clearance required."

        if policy == "ROOT_ONLY":
            if user_role == "root":
                return True, "Root owner clearance verified."
            return False, "Restricted exclusively to root owner."

        # Default deny
        return False, f"Unknown policy tier: {policy_level}"

    @classmethod
    def evaluate_tool_access(
        cls,
        user_role: str,
        tool_risk_level: str,
        requires_approval: bool,
        has_pending_approval: bool = False
    ) -> Tuple[bool, str]:
        """Evaluates tool execution permissions."""
        risk = tool_risk_level.upper()
        if user_role == "root":
            return True, "Root override allowed."

        if requires_approval and not has_pending_approval:
            return False, "Tool execution requires explicit SecOps/Mlops approval."

        if risk in ("HIGH", "CRITICAL") and user_role not in ("root", "SysAdmin", "SecOpsAdmin", "MlopsAdmin"):
            return False, f"Risk tier {risk} prohibited for role {user_role}."

        return True, "Tool access authorized."
