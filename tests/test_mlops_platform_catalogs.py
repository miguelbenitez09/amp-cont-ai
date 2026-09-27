"""
MLOps Platform 5-Way Catalog Separation Tests — amp-cont-ai
Verifies Section 2 of Plan Maestro:
  A. Model Registry
  B. Runtime Model Catalog
  C. Benchmark Catalog
  D. Model Access Catalog
  E. Model Deployment Catalog
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

import pytest
from src.platform.models.catalog import ModelCatalogService
from src.platform.policies import AccessPolicyEngine


def test_catalogs_are_independent_and_distinct():
    """Validates that the 5 catalogs return separate structures and are not unified in a single dictionary."""
    service = ModelCatalogService()

    registry = service.get_model_registry()
    runtime_cat = service.get_runtime_catalog()
    benchmarks = service.get_benchmark_catalog()
    access = service.get_access_catalog()
    deployments = service.get_deployment_catalog()

    assert isinstance(registry, list)
    assert isinstance(runtime_cat, list)
    assert isinstance(benchmarks, list)
    assert isinstance(access, list)
    assert isinstance(deployments, list)

    # Validate registry has version and status
    assert len(registry) > 0
    assert hasattr(registry[0], "version")
    assert hasattr(registry[0], "status")

    # Validate runtime catalog attaches live health inspection
    assert len(runtime_cat) > 0
    assert "runtime_health" in runtime_cat[0]
    assert "status" in runtime_cat[0]["runtime_health"]

    # Validate benchmark catalog contains empirical metrics
    assert len(benchmarks) == 8
    champion = next(b for b in benchmarks if b["champion"])
    assert champion["algorithm"] == "LightGBM Quantile Regressor"
    assert champion["wape"] < 0.09

    # Validate access catalog defines policies and allowed roles
    assert len(access) > 0
    assert "policy" in access[0]
    assert "allowed_roles" in access[0]

    # Validate deployments catalog has ports and runtimes
    assert len(deployments) > 0
    assert "port" in deployments[0]
    assert "runtime_id" in deployments[0]


def test_access_policy_engine_hierarchy():
    """Validates ABAC/RBAC permission checks across role tiers."""
    # Public models
    ok, _ = AccessPolicyEngine.evaluate_model_access("Guest", "PUBLIC")
    assert ok is True

    # Authenticated models
    ok, _ = AccessPolicyEngine.evaluate_model_access("Guest", "AUTHENTICATED")
    assert ok is False

    ok, _ = AccessPolicyEngine.evaluate_model_access("Analyst", "AUTHENTICATED")
    assert ok is True

    # Verified User (Requires MFA)
    ok, _ = AccessPolicyEngine.evaluate_model_access("Analyst", "VERIFIED_USER", is_mfa_authenticated=False)
    assert ok is False

    ok, _ = AccessPolicyEngine.evaluate_model_access("Analyst", "VERIFIED_USER", is_mfa_authenticated=True)
    assert ok is True

    # Role Restricted (MlopsAdmin / Root)
    ok, _ = AccessPolicyEngine.evaluate_model_access("SysAdmin", "ROLE_RESTRICTED")
    assert ok is False

    ok, _ = AccessPolicyEngine.evaluate_model_access("MlopsAdmin", "ROLE_RESTRICTED")
    assert ok is True

    ok, _ = AccessPolicyEngine.evaluate_model_access("root", "ROLE_RESTRICTED")
    assert ok is True
