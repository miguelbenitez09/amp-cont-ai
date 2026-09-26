"""
Database Seeder for Panama PortOps-AI v2.0
Populates roles, permissions, role_permissions, and authoritative data sources idempotently.
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import sys
import sqlite3
import yaml
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = ROOT_DIR / "config"


def seed_database(conn: sqlite3.Connection) -> None:
    """Seeds roles, permissions, role_permissions and sources idempotently."""
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).isoformat()

    # 1. Load roles.yaml
    roles_file = CONFIG_DIR / "roles.yaml"
    if roles_file.exists():
        with open(roles_file, "r", encoding="utf-8") as f:
            roles_data = yaml.safe_load(f).get("roles", [])
            for r in roles_data:
                cursor.execute("""
                INSERT INTO roles (role_id, role_name, tier, is_assignable, requires_mfa, description)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(role_id) DO UPDATE SET
                    role_name=excluded.role_name,
                    tier=excluded.tier,
                    is_assignable=excluded.is_assignable,
                    requires_mfa=excluded.requires_mfa,
                    description=excluded.description;
                """, (r["id"], r["name"], r["tier"], int(r.get("is_assignable", True)), int(r.get("requires_mfa", False)), r.get("description", "")))

    # 2. Load permissions.yaml
    perms_file = CONFIG_DIR / "permissions.yaml"
    if perms_file.exists():
        with open(perms_file, "r", encoding="utf-8") as f:
            perms_cfg = yaml.safe_load(f)
            perms_data = perms_cfg.get("permissions", [])
            for p in perms_data:
                cursor.execute("""
                INSERT INTO permissions (permission_id, resource, action, description)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(permission_id) DO UPDATE SET
                    resource=excluded.resource,
                    action=excluded.action,
                    description=excluded.description;
                """, (p["id"], p["resource"], p["action"], p.get("description", "")))

            # Seed role_permissions
            mappings = perms_cfg.get("role_permission_mappings", {})
            for role_id, perm_patterns in mappings.items():
                for pattern in perm_patterns:
                    if pattern == "*":
                        # All permissions
                        for p in perms_data:
                            cursor.execute("""
                            INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                            VALUES (?, ?);
                            """, (role_id, p["id"]))
                    elif pattern.endswith(".*"):
                        prefix = pattern[:-2]
                        for p in perms_data:
                            if p["id"].startswith(prefix + ".") or p["resource"] == prefix:
                                cursor.execute("""
                                INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                                VALUES (?, ?);
                                """, (role_id, p["id"]))
                    else:
                        cursor.execute("""
                        INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                        VALUES (?, ?);
                        """, (role_id, pattern))

    # 3. Load data_sources.yaml
    sources_file = CONFIG_DIR / "data_sources.yaml"
    if sources_file.exists():
        with open(sources_file, "r", encoding="utf-8") as f:
            sources_data = yaml.safe_load(f).get("sources", [])
            for s in sources_data:
                cursor.execute("""
                INSERT INTO data_sources (
                    source_id, name, organization, source_type, base_url, dataset_url,
                    owner, license, refresh_frequency, schema_version, status, trust_level,
                    enabled, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    name=excluded.name,
                    organization=excluded.organization,
                    dataset_url=excluded.dataset_url,
                    status=excluded.status,
                    enabled=excluded.enabled;
                """, (
                    s["id"], s["name"], s["organization"], s["source_type"], s["base_url"], s["dataset_url"],
                    s["owner"], s["license"], s["refresh_frequency"], s["schema_version"], s.get("status", "active"),
                    s["trust_level"], int(s.get("enabled", True)), now_str
                ))

    # 4. Seed Champion Model in model_registry
    cursor.execute("""
    INSERT INTO model_registry (
        model_id, model_name, version_tag, algorithm, dataset_hash, parameters_json,
        wape_score, mae_score, rmse_score, r2_score, pinball_loss,
        status, is_champion, created_by, approved_by, created_at, updated_at
    ) VALUES (
        'lightgbm_quantile_champion_v1',
        'LightGBM Quantile Ensemble (P10/P50/P90)',
        'v1.0.0',
        'LightGBM Quantile Regressor',
        'a7c92b8d4e1f6a0b8c2d4e6f8a0b2c4d6e8f0a2b4c6d8e0f2a4b6c8d0e2f4a6b',
        '{"n_estimators": 120, "learning_rate": 0.05, "max_depth": 6, "num_leaves": 31, "quantiles": [0.1, 0.5, 0.9]}',
        0.0911,
        14250.0,
        18500.0,
        0.983,
        0.042,
        'PRODUCTION',
        1,
        'mlops_engineer',
        'ml_reviewer',
        ?, ?
    ) ON CONFLICT(model_id) DO UPDATE SET
        status=excluded.status,
        is_champion=excluded.is_champion,
        updated_at=excluded.updated_at;
    """, (now_str, now_str))

    # 5. Seed Genesis Block in audit_ledger_worm if table is empty
    cursor.execute("SELECT COUNT(*) FROM audit_ledger_worm;")
    worm_count = cursor.fetchone()[0]
    if worm_count == 0:
        import hashlib
        import json
        genesis_prev = "0" * 64
        genesis_payload = json.dumps({"event": "GENESIS_INITIALIZATION", "author": "Desarrollado v1.0 Miguel Benitez", "timestamp": now_str}, sort_keys=True)
        genesis_hash = hashlib.sha256(f"{genesis_prev}|root|{genesis_payload}|{now_str}".encode()).hexdigest()
        cursor.execute("""
        INSERT INTO audit_ledger_worm (
            prev_block_hash, block_hash, event_type, actor_username, actor_role, payload_hash, payload_json, ip_origin, created_at
        ) VALUES (?, ?, 'GENESIS_BLOCK', 'root', 'root', ?, ?, '127.0.0.1', ?);
        """, (genesis_prev, genesis_hash, hashlib.sha256(genesis_payload.encode()).hexdigest(), genesis_payload, now_str))

    # 6. Seed Default Model Access Policies
    default_policies = [
        ("pol_root_all", "root", "*", 8192, 50000, 10000000, '["*"]', 0, 1),
        ("pol_admin_all", "admin", "*", 4096, 20000, 5000000, '["*"]', 0, 1),
        ("pol_mlops_all", "mlops_engineer", "*", 4096, 10000, 2000000, '["get_port_forecast", "query_hscode_panama", "run_monte_carlo_risk_simulation"]', 0, 1),
        ("pol_reviewer_all", "ml_reviewer", "*", 4096, 5000, 1000000, '["get_port_forecast", "query_hscode_panama"]', 0, 1),
        ("pol_auditor_all", "maritime_auditor", "*", 4096, 5000, 1000000, '["query_hscode_panama", "get_port_forecast"]', 0, 1),
        ("pol_operator_all", "terminal_operator", "*", 2048, 2500, 500000, '["get_port_forecast"]', 0, 1),
        ("pol_analyst_all", "port_analyst", "*", 2048, 2500, 500000, '["get_port_forecast", "query_hscode_panama"]', 0, 1),
        ("pol_viewer_all", "readonly_viewer", "*", 1024, 1000, 200000, '[]', 0, 1),
    ]
    for p in default_policies:
        cursor.execute("""
        INSERT INTO model_access_policies (
            policy_id, role_id, model_name, max_tokens_per_req, daily_request_limit, daily_token_limit, allowed_tools, requires_approval, is_active, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(policy_id) DO UPDATE SET
            max_tokens_per_req=excluded.max_tokens_per_req,
            daily_request_limit=excluded.daily_request_limit,
            daily_token_limit=excluded.daily_token_limit,
            allowed_tools=excluded.allowed_tools;
        """, (*p, now_str))

    conn.commit()


if __name__ == "__main__":
    db_path = ROOT_DIR / "data" / "enterprise_db" / "portops_platform.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    seed_database(conn)
    print("Database seeding completed successfully.")
    conn.close()
