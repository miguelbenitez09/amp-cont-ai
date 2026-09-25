"""
Panama PortOps-AI Executive Simulation & MLOps Control Dashboard.
Built with Streamlit (100% Open Source, Docker Compatible).
Simulates full end-to-end MLOps architecture:
- Real-time quantile forecasting (P10, P50, P90)
- What-If scenario perturbation engine
- Empty container imbalance alerting
- Model Registry & Drift Observability
"""

import os
import json
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import joblib

st.set_page_config(
    page_title="Panama PortOps-AI | MLOps Platform",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
REPORTS_DIR = PROJECT_ROOT / "reports"

VALID_PORTS = [
    "Puerto Balboa",
    "SSA Marine MIT",
    "PSA Panama International Terminal",
    "Colon Container Terminal",
    "Puerto Cristóbal",
    "Bocas Fruit Co."
]

@st.cache_resource
def load_ml_bundle():
    bundle_path = MODELS_DIR / "champion_models.joblib"
    if not bundle_path.exists():
        return None
    return joblib.load(bundle_path)

@st.cache_data
def load_gold_features():
    feat_path = GOLD_DIR / "container_features.parquet"
    if not feat_path.exists():
        return None
    return pd.read_parquet(feat_path)

bundle = load_ml_bundle()
features_df = load_gold_features()

# --- Sidebar Controls ---
st.sidebar.image("https://img.icons8.com/color/96/cargo-ship.png", width=70)
st.sidebar.title("🚢 Panama PortOps-AI")
st.sidebar.caption("Desarrollado v1.0 Miguel Benítez")
st.sidebar.markdown("**Sistema MLOps de Inteligencia Portuaria**")
st.sidebar.markdown("---")

selected_port = st.sidebar.selectbox("Seleccione Terminal Portuaria:", VALID_PORTS, index=0)
horizon_months = st.sidebar.slider("Horizonte de Pronóstico (Meses):", min_value=1, max_value=6, value=3)

st.sidebar.markdown("### ⚙️ Simulación de Escenarios (What-If)")
what_if_bunker = st.sidebar.slider("Perturbación Ventas Bunkering (%):", min_value=-50, max_value=50, value=0, step=5)
what_if_trans = st.sidebar.slider("Perturbación Ratio Trasbordo (%):", min_value=-30, max_value=30, value=0, step=5)

st.sidebar.markdown("---")
st.sidebar.markdown("**Estado del Ecosistema MLOps:**")
st.sidebar.success("🟢 Modelo: Champion v1 (LightGBM Cuantiles)")
st.sidebar.info("📦 Feature Store: 85 Features (Gold)")
st.sidebar.caption("Datos: Autoridad Marítima de Panamá (2015-2026)")
st.sidebar.caption("Marco Legal: Ley 6 de 2002 de Transparencia (Panamá)")

# --- Main Layout ---
st.title("🇵🇦 Panamá PortOps-AI: Control Operativo y Pronóstico de Demanda")
st.caption("Firma Oficial: Desarrollado v1.0 Miguel Benítez | Fines Cívicos y Educativos (Ley 6 de 2002)")
st.markdown(
    "Plataforma integral de **Machine Learning en Producción (MLOps)** para la predicción de tráfico de contenedores (TEUs), "
    "dimensionamiento de capacidad de muelle y simulación de resiliencia en el hub interoceánico de Panamá. "
    "**100% Datos Reales (Zero Mocks)** basados en 140 meses de microdatos oficiales de la AMP."
)

if bundle is None or features_df is None:
    st.error("No se encontraron los modelos o el Feature Store. Ejecute 'make all' para generar los artefactos.")
    st.stop()

models = bundle["models"]
feature_cols = bundle["feature_cols"]

# Filter data for selected port
port_hist = features_df[features_df["port"] == selected_port].sort_values(by="date").reset_index(drop=True)
latest_obs = port_hist.iloc[-1]
latest_date = latest_obs["date"]

# Prepare inference row with One-Hot encoding
df_encoded = pd.get_dummies(features_df, columns=["port", "littoral"], drop_first=False)
port_encoded_row = df_encoded[df_encoded["port_" + selected_port] == 1].iloc[-1:].copy()

# Apply What-If perturbations
if what_if_bunker != 0 and "nat_vlsfo_sales_tm_lag1" in port_encoded_row.columns:
    port_encoded_row["nat_vlsfo_sales_tm_lag1"] *= (1.0 + what_if_bunker / 100.0)

if what_if_trans != 0 and "transshipment_ratio_lag_1" in port_encoded_row.columns:
    port_encoded_row["transshipment_ratio_lag_1"] = np.clip(
        port_encoded_row["transshipment_ratio_lag_1"] * (1.0 + what_if_trans / 100.0), 0.0, 1.0
    )

# Multi-horizon forecasting
curr_feat = port_encoded_row[feature_cols].fillna(0).copy()
forecast_records = []

for step in range(1, horizon_months + 1):
    target_date = latest_date + pd.DateOffset(months=step)
    p50_val = float(models["p50"].predict(curr_feat)[0])
    p10_val = float(models["p10"].predict(curr_feat)[0])
    p90_val = float(models["p90"].predict(curr_feat)[0])
    
    # Monotonicity check
    p10_val = max(0.0, min(p10_val, p50_val))
    p90_val = max(p50_val, p90_val)
    p50_val = max(0.0, p50_val)
    
    forecast_records.append({
        "date": target_date,
        "month_str": target_date.strftime("%Y-%m"),
        "step": step,
        "p10": p10_val,
        "p50": p50_val,
        "p90": p90_val
    })
    
    if "teu_total_lag_1" in curr_feat.columns:
        curr_feat["teu_total_lag_1"] = p50_val

df_forecast = pd.DataFrame(forecast_records)

# --- Top KPIs ---
c1, c2, c3, c4 = st.columns(4)
next_month_p50 = df_forecast.iloc[0]["p50"]
next_month_p10 = df_forecast.iloc[0]["p10"]
next_month_p90 = df_forecast.iloc[0]["p90"]
prev_month_actual = latest_obs["teu_total"]
mom_pct = ((next_month_p50 - prev_month_actual) / prev_month_actual) * 100

c1.metric("Pronóstico Próximo Mes (P50)", f"{next_month_p50:,.0f} TEUs", f"{mom_pct:+.1f}% vs Último Real")
c2.metric("Suelo de Incertidumbre (P10)", f"{next_month_p10:,.0f} TEUs", "Riesgo Mínimo (10%)")
c3.metric("Capacidad Pico / Estrés (P90)", f"{next_month_p90:,.0f} TEUs", "Riesgo Máximo (90%)")

empty_ratio_val = latest_obs.get("empty_ratio", 0.5)
if empty_ratio_val > 0.8:
    c4.metric("Estado de Vacíos", f"{empty_ratio_val:.2f}", "⚠️ Superávit Crítico")
elif empty_ratio_val < 0.2:
    c4.metric("Estado de Vacíos", f"{empty_ratio_val:.2f}", "🟡 Déficit de Cajas")
else:
    c4.metric("Estado de Vacíos", f"{empty_ratio_val:.2f}", "🟢 Balance Óptimo")

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Pronóstico Multi-Horizonte con Incertidumbre",
    "🔬 Simulador What-If y Sensibilidad",
    "📦 Desbalance de Contenedores Vacíos",
    "🛡️ MLOps Governance & Observability",
    "🎲 Simulación Monte Carlo y Pruebas de Estrés"
])

# Tab 1: Forecasting Chart
with tab1:
    st.subheader(f"Proyección de Movimiento de TEUs: {selected_port}")
    
    # Filter last 24 months of history
    hist_tail = port_hist.tail(24)
    
    fig = go.Figure()
    
    # Historical Trace
    fig.add_trace(go.Scatter(
        x=hist_tail["date"],
        y=hist_tail["teu_total"],
        mode="lines+markers",
        name="Histórico Real (AMP)",
        line=dict(color="#1f77b4", width=3),
        marker=dict(size=6)
    ))
    
    # Quantile P90
    fig.add_trace(go.Scatter(
        x=df_forecast["date"],
        y=df_forecast["p90"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        name="P90 (Techo)"
    ))
    
    # Quantile P10 (fills to P90)
    fig.add_trace(go.Scatter(
        x=df_forecast["date"],
        y=df_forecast["p10"],
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(255, 127, 14, 0.25)",
        name="Intervalo Incertidumbre (P10 - P90)"
    ))
    
    # Quantile P50 (Forecast)
    fig.add_trace(go.Scatter(
        x=df_forecast["date"],
        y=df_forecast["p50"],
        mode="lines+markers",
        name="Pronóstico Central (P50 LightGBM)",
        line=dict(color="#ff7f0e", width=3, dash="dash"),
        marker=dict(size=8, symbol="diamond")
    ))
    
    fig.update_layout(
        title=f"Curva de Demanda y Abanico de Incertidumbre — {selected_port}",
        xaxis_title="Fecha (Año-Mes)",
        yaxis_title="Volumen Mensual (TEUs)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Table of Forecasts
    st.markdown("#### Detalle Tabular del Pronóstico")
    table_df = df_forecast[["month_str", "step", "p10", "p50", "p90"]].copy()
    table_df.columns = ["Mes Objetivo", "Horizonte (Meses)", "P10 (Pessimistic)", "P50 (Median Forecast)", "P90 (Peak Capacity)"]
    st.dataframe(table_df.style.format({
        "P10 (Pessimistic)": "{:,.0f} TEUs",
        "P50 (Median Forecast)": "{:,.0f} TEUs",
        "P90 (Peak Capacity)": "{:,.0f} TEUs"
    }), use_container_width=True)

# Tab 2: What-If Simulation
with tab2:
    st.subheader("Simulador de Resiliencia y Sensibilidad de la Cadena de Suministro")
    st.markdown(
        "Permite evaluar cómo choques externos en el hub de Panamá (cambios en ventas de combustible marino o "
        "caídas de trasbordo por desvío de rutas) impactan el volumen proyectado de la terminal."
    )
    
    if what_if_bunker == 0 and what_if_trans == 0:
        st.info("ℹ️ Ajuste los deslizadores de la barra lateral izquierda ('Simulación de Escenarios') para aplicar choques de sensibilidad.")
    else:
        st.warning(f"⚠️ Escenario Activo: Bunkering ({what_if_bunker:+d}%) | Trasbordo ({what_if_trans:+d}%)")
        
    diff_teu = df_forecast.iloc[0]["p50"] - (prev_month_actual)
    st.write(f"**Impacto estimado en el primer mes proyectado:** `{diff_teu:+,.0f} TEUs` frente al último dato observado.")

# Tab 3: Empty Container Imbalance
with tab3:
    st.subheader("Diagnóstico de Reposicionamiento y Almacenamiento de Contenedores Vacíos")
    st.markdown(
        "El desbalance de cajas vacías es uno de los mayores costos ocultos de las navieras. "
        "Cuando el ratio **`Vacíos / Llenos` supera 0.8**, la terminal se encuentra en **Superávit Crítico**, requiriendo buques de evacuación."
    )
    
    fig_empty = go.Figure()
    fig_empty.add_trace(go.Scatter(
        x=port_hist["date"],
        y=port_hist["empty_ratio"],
        mode="lines",
        name="Empty Ratio Histórico (Vacíos / Llenos)",
        line=dict(color="#2ca02c", width=2)
    ))
    fig_empty.add_hline(y=0.8, line_dash="dash", line_color="red", annotation_text="Umbral Crítico de Superávit (0.8)")
    fig_empty.add_hline(y=0.2, line_dash="dash", line_color="orange", annotation_text="Umbral de Déficit (0.2)")
    fig_empty.update_layout(
        title=f"Evolución del Ratio de Contenedores Vacíos vs Llenos — {selected_port}",
        yaxis_title="Ratio (Vacíos / Llenos)",
        xaxis_title="Fecha",
        template="plotly_white",
        height=450
    )
    st.plotly_chart(fig_empty, use_container_width=True)

# Tab 4: MLOps Governance & Observability
with tab4:
    st.subheader("Gobernanza del Ciclo de Vida MLOps y Observabilidad en Producción")
    
    col_gov1, col_gov2 = st.columns(2)
    
    with col_gov1:
        st.markdown("#### 🏛️ MLflow Model Registry")
        summary_path = MODELS_DIR / "training_summary.json"
        if summary_path.exists():
            with open(summary_path, "r", encoding="utf-8") as f:
                sum_data = json.load(f)
            st.json(sum_data)
            
    with col_gov2:
        st.markdown("#### 🔍 Evidently AI — Reporte de Data Drift")
        drift_summary_path = REPORTS_DIR / "data_drift_summary.json"
        if drift_summary_path.exists():
            with open(drift_summary_path, "r", encoding="utf-8") as f:
                drift_data = json.load(f)
            st.json(drift_data)
            
            html_report = REPORTS_DIR / "data_drift_report.html"
            if html_report.exists():
                st.success(f"Reporte visual HTML disponible en: `{html_report}`")
                
    st.markdown("#### 📊 Importancia de Variables en el Modelo Champion")
    feat_img_path = MODELS_DIR / "feature_importance.png"
    if feat_img_path.exists():
        st.image(str(feat_img_path), caption="Top 20 Variables con Mayor Ganancia Predictiva (LightGBM P50)", use_container_width=True)

# Tab 5: Monte Carlo Simulation & Stress Testing
with tab5:
    st.subheader(f"🎲 Motor de Simulación Estocástica y Pruebas de Estrés — {selected_port}")
    st.markdown(
        "Evalúa la solidez y resiliencia del modelo predictivo frente a choques extremos multivariados (*Black Swan Events*). "
        "Utiliza **descomposición de Cholesky** para preservar correlaciones históricas, **procesos de difusión con saltos de Merton (1976)** "
        "para modelar disrupciones del Canal de Panamá, y cuantifica métricas de riesgo financiero/logístico (**VaR 95%** y **CVaR / Expected Shortfall**)."
    )
    
    col_sim_cfg1, col_sim_cfg2, col_sim_cfg3 = st.columns(3)
    with col_sim_cfg1:
        sim_scenario = st.selectbox(
            "Seleccione Escenario Estocástico:",
            [
                ("baseline", "🟢 Baseline Estocástico (Histórico Normal)"),
                ("canal_drought", "📉 Sequía en Canal (-35% Trasbordo + Saltos Poisson)"),
                ("empty_imbalance", "📦 Desbalance Crítico (+45% Cajas Vacías)"),
                ("bunker_crisis", "⛽ Crisis de Combustible (+80% Volatilidad)"),
                ("black_swan_compound", "🌪️ Choque Extremo Compuesto (-45% Trasbordo, +50% Vacíos)")
            ],
            format_func=lambda x: x[1]
        )[0]
        
    with col_sim_cfg2:
        sim_paths = st.select_slider("Número de Trayectorias Monte Carlo:", options=[50, 100, 200, 500], value=100)
        
    with col_sim_cfg3:
        sim_horizon = st.slider("Horizonte de Simulación (Meses):", min_value=3, max_value=12, value=6)

    # Simulation Execution
    if st.button("🚀 Ejecutar Simulación Monte Carlo", type="primary", use_container_width=True):
        with st.spinner(f"Generando {sim_paths} trayectorias estocásticas para {selected_port}..."):
            try:
                from src.simulation.stress_tester import PortStressTester
                tester = PortStressTester()
                sim_res = tester.run_stress_test(
                    port_name=selected_port,
                    horizon=sim_horizon,
                    num_paths=sim_paths,
                    scenarios=[sim_scenario]
                )
                st.session_state[f"sim_{selected_port}_{sim_scenario}"] = sim_res
                st.success("✅ Simulación completada con éxito.")
            except Exception as e:
                st.error(f"Error al ejecutar la simulación: {e}")

    # Retrieve cached simulation result or run default
    sim_data_key = f"sim_{selected_port}_{sim_scenario}"
    if sim_data_key not in st.session_state:
        # Check if precomputed in metadata
        precomputed_file = Path("data/metadata/stress_test_results.json")
        if precomputed_file.exists() and selected_port == "Puerto Balboa":
            try:
                with open(precomputed_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                if sim_scenario in cached.get("stress_results", {}).get("scenarios", {}):
                    st.session_state[sim_data_key] = {
                        "port_name": selected_port,
                        "horizon_months": 6,
                        "num_paths": 100,
                        "scenarios": {sim_scenario: cached["stress_results"]["scenarios"][sim_scenario]}
                    }
            except Exception:
                pass

    if sim_data_key in st.session_state:
        res = st.session_state[sim_data_key]
        sc_data = res["scenarios"][sim_scenario]
        
        # Risk Metric Cards
        st.markdown("### 🛡️ Métricas de Riesgo y Colas de Pérdida (Horizonte Final)")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Volumen Medio Esperado", f"{sc_data['expected_volume']:,.0f} TEUs", f"σ = {sc_data['volatility_std']:,.0f}")
        m2.metric("Value at Risk (VaR 95%)", f"{sc_data['var_95_volume']:,.0f} TEUs", "Piso de Seguridad al 95%")
        m3.metric("Expected Shortfall (CVaR 95%)", f"{sc_data['cvar_95_expected_shortfall']:,.0f} TEUs", "Pérdida en Cola Peor 5%", delta_color="inverse")
        m4.metric("Probabilidad Caída > 25%", f"{sc_data['prob_severe_drop_25pct']*100:.1f}%", "Riesgo de Estrangulamiento")

        # 1. Fan Chart of Trajectories
        st.markdown("### 📈 Abanico de Trayectorias Estocásticas (Fan Chart)")
        traj_df = pd.DataFrame(sc_data["trajectory_profile"])
        
        fig_fan = go.Figure()
        # Historical context (last 12 months)
        hist_tail12 = port_hist.tail(12)
        fig_fan.add_trace(go.Scatter(
            x=hist_tail12["date"],
            y=hist_tail12["teu_total"],
            mode="lines+markers",
            name="Histórico Real",
            line=dict(color="#1f77b4", width=2.5)
        ))
        
        # P10 - P90 Outer Band
        fig_fan.add_trace(go.Scatter(
            x=traj_df["forecast_date"],
            y=traj_df["p90"],
            mode="lines",
            line=dict(width=0),
            showlegend=False
        ))
        fig_fan.add_trace(go.Scatter(
            x=traj_df["forecast_date"],
            y=traj_df["p10"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(255, 127, 14, 0.20)",
            name="Banda 80% Confianza (P10 - P90)",
            line=dict(width=0)
        ))
        
        # P25 - P75 Inner Band
        fig_fan.add_trace(go.Scatter(
            x=traj_df["forecast_date"],
            y=traj_df["p75"],
            mode="lines",
            line=dict(width=0),
            showlegend=False
        ))
        fig_fan.add_trace(go.Scatter(
            x=traj_df["forecast_date"],
            y=traj_df["p25"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(255, 127, 14, 0.35)",
            name="Banda 50% Intercuartil (P25 - P75)",
            line=dict(width=0)
        ))
        
        # Central P50 Path
        fig_fan.add_trace(go.Scatter(
            x=traj_df["forecast_date"],
            y=traj_df["p50"],
            mode="lines+markers",
            name="Mediana Estocástica (P50)",
            line=dict(color="#d62728", width=3, dash="dash")
        ))
        
        fig_fan.update_layout(
            title=f"Cono de Dispersión Estocástica — {selected_port} ({sim_scenario.replace('_', ' ').title()})",
            xaxis_title="Fecha de Pronóstico",
            yaxis_title="Volumen Mensual (TEUs)",
            hovermode="x unified",
            template="plotly_white",
            height=480
        )
        st.plotly_chart(fig_fan, use_container_width=True)

        # 2. Distribution Density & VaR/CVaR Cutoffs
        col_dist1, col_dist2 = st.columns(2)
        with col_dist1:
            st.markdown("### 📊 Distribución de Probabilidad del Volumen Final")
            sample_endpoints = sc_data.get("endpoint_sample", [])
            if sample_endpoints:
                fig_hist = go.Figure()
                fig_hist.add_trace(go.Histogram(
                    x=sample_endpoints,
                    nbinsx=25,
                    name="Muestras Monte Carlo",
                    marker_color="#4682b4",
                    opacity=0.75
                ))
                # VaR 95% line
                fig_hist.add_vline(
                    x=sc_data["var_95_volume"],
                    line_dash="dash",
                    line_color="orange",
                    annotation_text=f"VaR 95%: {sc_data['var_95_volume']:,.0f}"
                )
                # CVaR 95% line
                fig_hist.add_vline(
                    x=sc_data["cvar_95_expected_shortfall"],
                    line_dash="dot",
                    line_color="red",
                    annotation_text=f"CVaR 95%: {sc_data['cvar_95_expected_shortfall']:,.0f}"
                )
                fig_hist.update_layout(
                    title="Histograma de TEUs en el Horizonte Final",
                    xaxis_title="Volumen Simulado (TEUs)",
                    yaxis_title="Frecuencia",
                    template="plotly_white",
                    height=380
                )
                st.plotly_chart(fig_hist, use_container_width=True)

        with col_dist2:
            st.markdown("### ⚡ Pruebas de Estrés Inversas (Reverse Stress Testing)")
            st.markdown(
                "Detecta las combinaciones críticas de **caída de trasbordo** y **aumento de contenedores vacíos** "
                "que provocan una caída superior al umbral crítico de tolerancia operacional."
            )
            rst_file = Path("data/metadata/stress_test_results.json")
            if rst_file.exists():
                try:
                    with open(rst_file, "r", encoding="utf-8") as f:
                        rst_full = json.load(f)
                    tipping = rst_full.get("rst_results", {}).get("tipping_point_boundaries", [])
                    if tipping:
                        tp_df = pd.DataFrame(tipping)[["transshipment_drop_pct", "empty_surge_pct", "projected_teu", "drop_percentage"]]
                        tp_df.columns = ["Caída Trasbordo (%)", "Alza Vacíos (%)", "TEUs Resultantes", "Caída Total (%)"]
                        st.dataframe(tp_df.style.format({
                            "Caída Trasbordo (%)": "-{:.1f}%",
                            "Alza Vacíos (%)": "+{:.1f}%",
                            "TEUs Resultantes": "{:,.0f}",
                            "Caída Total (%)": "-{:.1f}%"
                        }), use_container_width=True)
                    else:
                        st.info("No se detectaron brechas críticas dentro de los rangos explorados.")
                except Exception as ex:
                    st.caption(f"Detalle RST no disponible: {ex}")
            else:
                st.caption("Ejecute `make stress-test` para generar la matriz completa de Reverse Stress Testing.")
    else:
        st.info("Presione **'🚀 Ejecutar Simulación Monte Carlo'** para computar las trayectorias de riesgo para este puerto.")

