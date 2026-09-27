-- ==============================================================================
-- Panama PortOps-AI v1.0.0 - Migration 003: MLOps Platform Core
-- Author: Desarrollado v1.0.0 Miguel Benítez
-- License: GNU General Public License v3.0 (GPL-3.0) with Section 7 Mandatory Attribution
-- Target: SQLite & PostgreSQL Dual-Engine Compatibility
-- ==============================================================================

-- 1. Model Versions (Decoupled from generic model name)
CREATE TABLE IF NOT EXISTS model_versions (
    version_id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    version_tag TEXT NOT NULL,
    revision TEXT NOT NULL,
    artifact_hash TEXT NOT NULL,
    signature_json TEXT NOT NULL DEFAULT '{}',
    parameters_json TEXT NOT NULL DEFAULT '{}',
    git_commit TEXT,
    dataset_version TEXT,
    evaluation_id TEXT,
    lifecycle_state TEXT NOT NULL DEFAULT 'DRAFT', 
    -- 'DRAFT', 'TRAINED', 'VALIDATED', 'EVALUATED', 'REVIEW', 'APPROVED', 'STAGED', 'DEPLOYED', 'SERVING', 'DEPRECATED', 'ARCHIVED'
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (model_id) REFERENCES model_registry(model_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_model_versions_model_id ON model_versions(model_id);
CREATE INDEX IF NOT EXISTS idx_model_versions_state ON model_versions(lifecycle_state);

-- 2. Model Artifacts (Weights, signatures, preprocessors)
CREATE TABLE IF NOT EXISTS model_artifacts (
    artifact_id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_hash_sha256 TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    artifact_type TEXT NOT NULL, -- 'weights', 'onnx', 'joblib', 'gguf', 'tokenizer', 'metadata'
    storage_backend TEXT NOT NULL DEFAULT 'local', -- 'local', 's3', 'minio'
    created_at TEXT NOT NULL,
    FOREIGN KEY (version_id) REFERENCES model_versions(version_id) ON DELETE CASCADE
);

-- 3. Model Evaluations & Benchmark Runs
CREATE TABLE IF NOT EXISTS model_evaluations (
    eval_id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL,
    eval_type TEXT NOT NULL, -- 'TOURNAMENT_8', 'HOLDOUT_QUANTILE', 'DRIFT_KS', 'SAFETY_GUARD'
    dataset_id TEXT,
    metrics_json TEXT NOT NULL DEFAULT '{}',
    passed_gates INTEGER NOT NULL DEFAULT 1,
    evaluated_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (version_id) REFERENCES model_versions(version_id) ON DELETE CASCADE
);

-- 4. Model Aliases (e.g. 'champion', 'candidate', 'production')
CREATE TABLE IF NOT EXISTS model_aliases (
    alias_name TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    version_id TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (model_id) REFERENCES model_registry(model_id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES model_versions(version_id) ON DELETE CASCADE
);

-- 5. Runtime Instances & Probes
CREATE TABLE IF NOT EXISTS runtime_instances (
    runtime_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    runtime_type TEXT NOT NULL, -- 'vllm', 'ollama', 'in_process', 'external_api'
    endpoint TEXT NOT NULL,
    health_endpoint TEXT,
    status TEXT NOT NULL DEFAULT 'UNKNOWN', -- 'CONFIGURED', 'READY', 'HEALTHY', 'SERVING', 'DEGRADED', 'FAILED'
    gpu_profile_json TEXT NOT NULL DEFAULT '{}',
    latency_ms REAL DEFAULT 0.0,
    discovered_models_json TEXT NOT NULL DEFAULT '[]',
    last_probed_at TEXT,
    created_at TEXT NOT NULL
);

-- 6. Model Deployments
CREATE TABLE IF NOT EXISTS model_deployments (
    deployment_id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    version_id TEXT NOT NULL,
    runtime_id TEXT NOT NULL,
    serving_name TEXT NOT NULL,
    port INTEGER NOT NULL DEFAULT 8000,
    replicas INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'CONFIGURED', 'STARTING', 'HEALTHY', 'FAILED', 'STOPPED'
    verification_checklist_json TEXT NOT NULL DEFAULT '{}',
    deployed_by TEXT NOT NULL,
    deployed_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (model_id) REFERENCES model_registry(model_id),
    FOREIGN KEY (version_id) REFERENCES model_versions(version_id),
    FOREIGN KEY (runtime_id) REFERENCES runtime_instances(runtime_id)
);

-- 7. MCP Servers & Tools Registry
CREATE TABLE IF NOT EXISTS mcp_servers (
    server_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    transport TEXT NOT NULL DEFAULT 'stdio', -- 'stdio', 'sse', 'http'
    command TEXT NOT NULL,
    args_json TEXT NOT NULL DEFAULT '[]',
    env_vars_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'REGISTERED', -- 'REGISTERED', 'RUNNING', 'STOPPED', 'ERROR'
    last_health_check TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mcp_tools (
    tool_id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL,
    tool_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    input_schema_json TEXT NOT NULL DEFAULT '{}',
    risk_level TEXT NOT NULL DEFAULT 'LOW', -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    requires_approval INTEGER NOT NULL DEFAULT 0,
    approval_role TEXT,
    allowed_roles_json TEXT NOT NULL DEFAULT '["*"]',
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (server_id) REFERENCES mcp_servers(server_id) ON DELETE CASCADE
);

-- 8. Tool Access Requests
CREATE TABLE IF NOT EXISTS tool_access_requests (
    request_id TEXT PRIMARY KEY,
    tool_name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    justification TEXT NOT NULL,
    parameters_summary TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'APPROVED', 'REJECTED', 'EXECUTED'
    reviewed_by TEXT,
    reviewed_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 9. Agent Souls & Definitions
CREATE TABLE IF NOT EXISTS souls (
    soul_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0.0',
    persona TEXT NOT NULL,
    tone TEXT NOT NULL DEFAULT 'professional',
    constraints_json TEXT NOT NULL DEFAULT '[]',
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_definitions (
    agent_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    soul_id TEXT,
    role TEXT NOT NULL,
    allowed_tools_json TEXT NOT NULL DEFAULT '[]',
    system_prompt TEXT NOT NULL,
    temperature REAL NOT NULL DEFAULT 0.2,
    created_at TEXT NOT NULL,
    FOREIGN KEY (soul_id) REFERENCES souls(soul_id)
);

-- 10. Model Access Rules (ABAC Policy Engine)
CREATE TABLE IF NOT EXISTS model_access_rules (
    rule_id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    access_policy TEXT NOT NULL DEFAULT 'PUBLIC', -- 'PUBLIC', 'AUTHENTICATED', 'VERIFIED_USER', 'ROLE_RESTRICTED', 'ADMIN_ONLY', 'ROOT_ONLY'
    allowed_roles_json TEXT NOT NULL DEFAULT '["*"]',
    allowed_depts_json TEXT NOT NULL DEFAULT '["*"]',
    require_mfa INTEGER NOT NULL DEFAULT 0,
    max_context_tokens INTEGER NOT NULL DEFAULT 2048,
    rate_limit_rpm INTEGER NOT NULL DEFAULT 60,
    created_at TEXT NOT NULL,
    FOREIGN KEY (model_id) REFERENCES model_registry(model_id) ON DELETE CASCADE
);
