-- ============================================================================
-- PANAMA PORTOPS-AI MLOPS ADVANCED ENTERPRISE DATABASE SCHEMA
-- PostgreSQL / TimescaleDB Enterprise Edition
-- Autor: Desarrollado v1.0 Miguel Benítez
-- Licencia: GNU General Public License v3.0 (GPL-3.0)
-- Características: Tablas Normalizadas, Inmutabilidad WORM, Triggers de Auditoría
-- ============================================================================

-- Extensión para generación de UUIDs y funciones criptográficas
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ----------------------------------------------------------------------------
-- 1. TABLA DE MODELOS MLOPS Y LINAJE (ml_models)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ml_models (
    model_id VARCHAR(64) PRIMARY KEY,
    model_name VARCHAR(128) NOT NULL,
    version_tag VARCHAR(32) NOT NULL,
    algorithm VARCHAR(64) NOT NULL,
    framework VARCHAR(64) NOT NULL DEFAULT 'LightGBM/Scikit-Learn',
    objective_loss VARCHAR(64) NOT NULL DEFAULT 'quantile_pinball',
    hyperparameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    features_count INT NOT NULL DEFAULT 85,
    wape_score NUMERIC(6, 4),
    r2_score NUMERIC(6, 4),
    p10_loss NUMERIC(10, 4),
    p50_loss NUMERIC(10, 4),
    p90_loss NUMERIC(10, 4),
    latency_ms NUMERIC(6, 2) NOT NULL DEFAULT 9.8,
    is_champion BOOLEAN NOT NULL DEFAULT FALSE,
    created_by VARCHAR(64) NOT NULL DEFAULT 'mlops_engineer',
    artifact_path VARCHAR(255) NOT NULL,
    sha256_checksum VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ml_models_algo ON ml_models(algorithm);
CREATE INDEX IF NOT EXISTS idx_ml_models_champion ON ml_models(is_champion);

-- ----------------------------------------------------------------------------
-- 2. CUOTAS DE RECURSOS Y GOBERNANZA POR USUARIO (user_resource_quotas)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_resource_quotas (
    username VARCHAR(64) PRIMARY KEY,
    role_name VARCHAR(32) NOT NULL,
    compute_tier VARCHAR(32) NOT NULL DEFAULT 'standard',
    max_concurrent_simulations INT NOT NULL DEFAULT 2,
    max_paths_per_run INT NOT NULL DEFAULT 10000,
    allowed_gpu BOOLEAN NOT NULL DEFAULT FALSE,
    total_runs_executed INT NOT NULL DEFAULT 0,
    total_cpu_seconds_consumed NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 3. HISTORIAL DE CORRIDAS DE SIMULACIÓN Y TELEMETRÍA (simulation_runs)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS simulation_runs (
    run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    executed_by VARCHAR(64) NOT NULL,
    model_id VARCHAR(64) REFERENCES ml_models(model_id) ON DELETE SET NULL,
    scenario_key VARCHAR(64) NOT NULL,
    scenario_title VARCHAR(128) NOT NULL,
    port_target VARCHAR(64) NOT NULL DEFAULT 'Sistema Portuario Nacional',
    horizon_months INT NOT NULL DEFAULT 6,
    synthetic_paths INT NOT NULL DEFAULT 2500,
    base_demand_s0 NUMERIC(12, 2) NOT NULL,
    drift_mu NUMERIC(6, 4) NOT NULL,
    volatility_sigma NUMERIC(6, 4) NOT NULL,
    jump_intensity_lambda NUMERIC(6, 4) NOT NULL DEFAULT 0.25,
    jump_magnitude_kappa NUMERIC(6, 4) NOT NULL DEFAULT -0.20,
    expected_volume_p50 NUMERIC(12, 2) NOT NULL,
    value_at_risk_var95 NUMERIC(12, 2) NOT NULL,
    conditional_var_cvar95 NUMERIC(12, 2) NOT NULL,
    severe_drop_probability NUMERIC(6, 4) NOT NULL,
    execution_time_ms NUMERIC(8, 2) NOT NULL,
    gpu_power_watts NUMERIC(6, 2) DEFAULT 0.0,
    memory_used_mb NUMERIC(8, 2) DEFAULT 45.2,
    hardware_device VARCHAR(32) DEFAULT 'CPU (OpenMP)',
    status VARCHAR(24) NOT NULL DEFAULT 'completed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sim_runs_user ON simulation_runs(executed_by);
CREATE INDEX IF NOT EXISTS idx_sim_runs_date ON simulation_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sim_runs_scenario ON simulation_runs(scenario_key);

-- ----------------------------------------------------------------------------
-- 4. LIBRO MAYOR INMUTABLE WORM (audit_ledger_worm)
-- Write-Once, Read-Many con encadenamiento criptográfico SHA-256
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_ledger_worm (
    block_id BIGSERIAL PRIMARY KEY,
    prev_block_hash VARCHAR(64) NOT NULL,
    block_hash VARCHAR(64) NOT NULL UNIQUE,
    event_type VARCHAR(64) NOT NULL,
    actor_username VARCHAR(64) NOT NULL,
    actor_role VARCHAR(32) NOT NULL,
    payload_json JSONB NOT NULL,
    ip_origin VARCHAR(45) NOT NULL DEFAULT '127.0.0.1',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_worm_event ON audit_ledger_worm(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_worm_date ON audit_ledger_worm(created_at DESC);

-- ----------------------------------------------------------------------------
-- 5. TRIGGER DE INMUTABILIDAD ESTRICTA WORM (Zero Update / Zero Delete)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_enforce_worm_immutability()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'VIOLACIÓN DE INTEGRIDAD WORM: La tabla audit_ledger_worm es estrictamente inmutable. No se permiten operaciones de UPDATE ni DELETE bajo la Ley 81 de 2019 y estándares ISO/IEC 27001.'
    USING ERRCODE = '23506';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_worm_no_tampering ON audit_ledger_worm;
CREATE TRIGGER trg_worm_no_tampering
BEFORE UPDATE OR DELETE ON audit_ledger_worm
FOR EACH ROW
EXECUTE FUNCTION trg_enforce_worm_immutability();

-- ----------------------------------------------------------------------------
-- 6. PROCEDIMIENTO PARA REGISTRAR EJECUCIÓN Y ACTUALIZAR CUOTA
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION sp_record_simulation_run(
    p_executed_by VARCHAR(64),
    p_model_id VARCHAR(64),
    p_scenario_key VARCHAR(64),
    p_scenario_title VARCHAR(128),
    p_port_target VARCHAR(64),
    p_horizon_months INT,
    p_synthetic_paths INT,
    p_base_demand NUMERIC(12, 2),
    p_drift NUMERIC(6, 4),
    p_volatility NUMERIC(6, 4),
    p_lambda NUMERIC(6, 4),
    p_kappa NUMERIC(6, 4),
    p_volume_p50 NUMERIC(12, 2),
    p_var95 NUMERIC(12, 2),
    p_cvar95 NUMERIC(12, 2),
    p_drop_prob NUMERIC(6, 4),
    p_exec_ms NUMERIC(8, 2),
    p_gpu_watts NUMERIC(6, 2),
    p_memory_mb NUMERIC(8, 2)
) RETURNS UUID AS $$
DECLARE
    v_run_id UUID;
    v_prev_hash VARCHAR(64);
    v_new_hash VARCHAR(64);
    v_payload JSONB;
BEGIN
    -- 1. Insertar corrida
    INSERT INTO simulation_runs (
        executed_by, model_id, scenario_key, scenario_title, port_target,
        horizon_months, synthetic_paths, base_demand_s0, drift_mu, volatility_sigma,
        jump_intensity_lambda, jump_magnitude_kappa, expected_volume_p50,
        value_at_risk_var95, conditional_var_cvar95, severe_drop_probability,
        execution_time_ms, gpu_power_watts, memory_used_mb
    ) VALUES (
        p_executed_by, p_model_id, p_scenario_key, p_scenario_title, p_port_target,
        p_horizon_months, p_synthetic_paths, p_base_demand, p_drift, p_volatility,
        p_lambda, p_kappa, p_volume_p50, p_var95, p_cvar95, p_drop_prob,
        p_exec_ms, p_gpu_watts, p_memory_mb
    ) RETURNING run_id INTO v_run_id;

    -- 2. Actualizar cuota de usuario
    UPDATE user_resource_quotas
    SET total_runs_executed = total_runs_executed + 1,
        total_cpu_seconds_consumed = total_cpu_seconds_consumed + (p_exec_ms / 1000.0),
        updated_at = NOW()
    WHERE username = p_executed_by;

    -- 3. Obtener hash anterior de la cadena WORM
    SELECT COALESCE((SELECT block_hash FROM audit_ledger_worm ORDER BY block_id DESC LIMIT 1),
                    '0000000000000000000000000000000000000000000000000000000000000000')
    INTO v_prev_hash;

    -- 4. Construir payload y computar hash SHA-256
    v_payload := jsonb_build_object(
        'run_id', v_run_id,
        'scenario', p_scenario_key,
        'var_95', p_var95,
        'cvar_95', p_cvar95,
        'exec_ms', p_exec_ms
    );
    v_new_hash := encode(digest(v_prev_hash || p_executed_by || v_payload::text || NOW()::text, 'sha256'), 'hex');

    -- 5. Insertar en libro mayor inmutable
    INSERT INTO audit_ledger_worm (
        prev_block_hash, block_hash, event_type, actor_username, actor_role, payload_json
    ) VALUES (
        v_prev_hash, v_new_hash, 'SIMULATION_EXECUTION_CERTIFIED', p_executed_by, 'port_operator', v_payload
    );

    RETURN v_run_id;
END;
$$ LANGUAGE plpgsql;

-- Datos de arranque iniciales
INSERT INTO user_resource_quotas (username, role_name, compute_tier, max_concurrent_simulations, max_paths_per_run, allowed_gpu)
VALUES 
    ('root', 'root_owner', 'unlimited', 10, 50000, TRUE),
    ('admin_amp', 'platform_admin', 'high_performance', 5, 25000, TRUE),
    ('operador_balboa', 'port_operator', 'standard', 2, 10000, FALSE),
    ('auditor_aig', 'compliance_auditor', 'audit_read', 1, 5000, FALSE)
ON CONFLICT (username) DO NOTHING;
