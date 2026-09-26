-- ==============================================================================
-- Panama PortOps-AI v1.0 - Migration 002: Inference Telemetry, Feedback & Policies
-- Author: Desarrollado v1.0 Miguel Benítez
-- License: GNU General Public License v3.0 (GPL-3.0) with Section 7 Mandatory Attribution
-- Target: SQLite & PostgreSQL Dual-Engine Compatibility
-- ==============================================================================

-- 1. Real Compute & Inference Telemetry Logs
CREATE TABLE IF NOT EXISTS inference_telemetry_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    runtime_engine TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    latency_ms REAL NOT NULL,
    compute_device TEXT NOT NULL,
    query_context TEXT,
    guardrail_verdict TEXT NOT NULL DEFAULT 'PASS',
    soul_id TEXT,
    ip_origin TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_telemetry_req_id ON inference_telemetry_logs(request_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_user_id ON inference_telemetry_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_created_at ON inference_telemetry_logs(created_at);

-- 2. User Interaction Feedback for Continuous Evaluation
CREATE TABLE IF NOT EXISTS model_interaction_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    rating_score INTEGER CHECK(rating_score BETWEEN 1 AND 5),
    is_positive INTEGER NOT NULL DEFAULT 1,
    feedback_category TEXT DEFAULT 'GENERAL',
    comments TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_feedback_req_id ON model_interaction_feedback(request_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON model_interaction_feedback(user_id);

-- 3. Model Access Policies & Quotas
CREATE TABLE IF NOT EXISTS model_access_policies (
    policy_id TEXT PRIMARY KEY,
    role_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    max_tokens_per_req INTEGER NOT NULL DEFAULT 2048,
    daily_request_limit INTEGER NOT NULL DEFAULT 1000,
    daily_token_limit INTEGER NOT NULL DEFAULT 100000,
    allowed_tools TEXT DEFAULT '[]',
    requires_approval INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_model_policies_role ON model_access_policies(role_id);
