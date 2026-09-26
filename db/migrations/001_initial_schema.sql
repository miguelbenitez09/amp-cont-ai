-- ==============================================================================
-- Panama PortOps-AI v2.0 - Complete Enterprise Schema Migration
-- Author: Desarrollado v1.0 Miguel Benítez
-- License: GNU General Public License v3.0 (GPL-3.0)
-- Target: SQLite & PostgreSQL Dual-Engine Compatibility
-- ==============================================================================

-- 1. Identity & Access Management (IAM)
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    is_root INTEGER NOT NULL DEFAULT 0,
    must_change_password INTEGER NOT NULL DEFAULT 0,
    mfa_enabled INTEGER NOT NULL DEFAULT 0,
    mfa_secret TEXT,
    recovery_code_hash TEXT,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roles (
    role_id TEXT PRIMARY KEY,
    role_name TEXT NOT NULL UNIQUE,
    tier TEXT NOT NULL,
    is_assignable INTEGER NOT NULL DEFAULT 1,
    requires_mfa INTEGER NOT NULL DEFAULT 0,
    description TEXT
);

CREATE TABLE IF NOT EXISTS permissions (
    permission_id TEXT PRIMARY KEY,
    resource TEXT NOT NULL,
    action TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id TEXT NOT NULL,
    permission_id TEXT NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(permission_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    assigned_by TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    ip_address TEXT,
    user_agent TEXT,
    expires_at TEXT NOT NULL,
    is_revoked INTEGER NOT NULL DEFAULT 0,
    last_activity_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS password_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS security_events (
    event_id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    ip_hash TEXT,
    user_agent_hash TEXT,
    result TEXT NOT NULL, -- 'SUCCESS', 'DENIED', 'FAILURE'
    reason TEXT,
    created_at TEXT NOT NULL
);

-- 2. Data Platform, Sources, Manifests & Lineage
CREATE TABLE IF NOT EXISTS data_sources (
    source_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    organization TEXT NOT NULL,
    source_type TEXT NOT NULL,
    base_url TEXT NOT NULL,
    dataset_url TEXT NOT NULL,
    owner TEXT NOT NULL,
    license TEXT NOT NULL,
    refresh_frequency TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    trust_level TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS datasets (
    dataset_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    name TEXT NOT NULL,
    layer TEXT NOT NULL, -- 'raw', 'bronze', 'silver', 'gold'
    version TEXT NOT NULL,
    schema_hash TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    min_date TEXT NOT NULL,
    max_date TEXT NOT NULL,
    quality_score REAL NOT NULL,
    classification TEXT NOT NULL DEFAULT 'FACT', -- 'FACT', 'MEASURED', 'DERIVED', 'ESTIMATED', 'SIMULATED', 'DEMO'
    created_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES data_sources(source_id)
);

CREATE TABLE IF NOT EXISTS dataset_lineage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id TEXT NOT NULL,
    parent_dataset_id TEXT,
    transformation TEXT NOT NULL,
    code_version TEXT NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (dataset_id) REFERENCES datasets(dataset_id)
);

-- 3. Model Registry, Experiments & Approvals
CREATE TABLE IF NOT EXISTS model_registry (
    model_id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    version_tag TEXT NOT NULL,
    algorithm TEXT NOT NULL,
    dataset_hash TEXT NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    wape_score REAL,
    mae_score REAL,
    rmse_score REAL,
    r2_score REAL,
    pinball_loss REAL,
    status TEXT NOT NULL DEFAULT 'TRAINED', -- 'DRAFT', 'TRAINED', 'VALIDATED', 'REVIEW', 'APPROVED', 'STAGED', 'PRODUCTION', 'RETIRED'
    is_champion INTEGER NOT NULL DEFAULT 0,
    created_by TEXT NOT NULL,
    approved_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS model_approvals (
    request_id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    target_environment TEXT NOT NULL DEFAULT 'production',
    status TEXT NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'APPROVED', 'REJECTED'
    reviewer_notes TEXT,
    approved_by TEXT,
    approved_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (model_id) REFERENCES model_registry(model_id)
);

-- 4. Simulation Runs & Risk Telemetry
CREATE TABLE IF NOT EXISTS simulation_runs (
    run_id TEXT PRIMARY KEY,
    executed_by TEXT NOT NULL,
    scenario_key TEXT NOT NULL,
    port_target TEXT NOT NULL,
    horizon_months INTEGER NOT NULL,
    synthetic_paths INTEGER NOT NULL,
    expected_volume_p50 REAL NOT NULL,
    var_95 REAL NOT NULL,
    cvar_95 REAL NOT NULL,
    severe_drop_prob REAL NOT NULL,
    execution_time_ms REAL NOT NULL,
    gpu_power_watts REAL DEFAULT 0.0,
    memory_used_mb REAL DEFAULT 45.2,
    hardware_device TEXT DEFAULT 'CPU (OpenMP)',
    status TEXT NOT NULL DEFAULT 'completed',
    created_at TEXT NOT NULL
);

-- 5. Cryptographic WORM Audit Ledger (Write Once, Read Many)
CREATE TABLE IF NOT EXISTS audit_ledger_worm (
    block_id INTEGER PRIMARY KEY AUTOINCREMENT,
    prev_block_hash TEXT NOT NULL,
    block_hash TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    actor_username TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    ip_origin TEXT NOT NULL DEFAULT '127.0.0.1',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_datasets_source ON datasets(source_id);
CREATE INDEX IF NOT EXISTS idx_models_champion ON model_registry(is_champion);
CREATE INDEX IF NOT EXISTS idx_worm_block_hash ON audit_ledger_worm(block_hash);
