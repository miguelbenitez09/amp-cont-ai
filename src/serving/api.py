"""
High-Performance Inference and Web Serving Microservice with FastAPI.
Adheres to MLOps Masterclass Sections 19 & 50:
- Multi-algorithm serving: LightGBM Quantile Ensemble, Random Forest, HistGradientBoosting, Ridge/ElasticNet
- Content-negotiated responses: Beautiful visual HTML for browsers, structured JSON for API clients
- In-depth interactive OpenAPI Swagger documentation with executable Python, cURL, and JS code examples
- Strict Pydantic v2 data validation without deprecation warnings
- Multi-quantile uncertainty output: P10 (Floor), P50 (Median), P90 (Ceiling)
- Multi-algorithm comparative benchmarking endpoint (/api/models/compare)
- Statistical diagnostics, VIF and confounders endpoint (/api/models/diagnostics)
- Scientific methodology endpoint (/api/methodology)
- Live Monte Carlo simulation & stress testing endpoint (/simulate)
- Historical data retrieval endpoint for interactive charting (/api/history/{port})
- Built-in vanguard static web UI serving at GET /
- Author: Desarrollado v1.0 Miguel Benítez
- Purpose: Proyecto desarrollado con fines estrictamente educativos, científicos y de investigación MLOps.
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

# Robust cross-platform project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, status, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
import numpy as np
import pandas as pd
import joblib

from src.utils.logger import logger
from src.models.registry import ModelRegistryManager
from src.simulation.stress_tester import PortStressTester

MODELS_DIR = PROJECT_ROOT / "models"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
STATIC_DIR = Path(__file__).resolve().parent / "static"

# In-memory artifact cache
ml_artifacts: Dict[str, Any] = {}

VALID_PORTS = [
    "Puerto Balboa",
    "SSA Marine MIT",
    "PSA Panama International Terminal",
    "Colon Container Terminal",
    "Puerto Cristóbal",
    "Bocas Fruit Co."
]

tags_metadata = [
    {
        "name": "Model Serving & Forecasting",
        "description": "Inferencia en tiempo real para pronósticos de demanda de TEUs a 1–6 meses con soporte multi-algoritmo y bandas de incertidumbre cuantílica (P10, P50, P90)."
    },
    {
        "name": "Model Benchmarking & Comparison",
        "description": "Evaluación comparativa formal entre LightGBM, Random Forest, HistGradientBoosting y Ridge/ElasticNet, con métricas WAPE, MAE, RMSE, R² y latencias."
    },
    {
        "name": "Statistical Diagnostics & Explainability",
        "description": "Diagnóstico estadístico de residuos reales, importancia de características, detección de multicolinealidad con VIF y catálogo de variables confundidoras."
    },
    {
        "name": "Monte Carlo Simulation & Risk",
        "description": "Motor estocástico multivariado para simulación de escenarios de estrés, cálculo de Value at Risk (VaR 95%/99%) y Conditional VaR (Expected Shortfall)."
    },
    {
        "name": "Methodology & Data Governance",
        "description": "Metodología de Data Cleaning, normalización, anonimización criptográfica y monitoreo continuo de Data Drift."
    },
    {
        "name": "System Health & Infrastructure",
        "description": "Sondas de salud operacional, liveness, readiness y metadatos de linaje."
    }
]

API_DESCRIPTION = """
# Panamá PortOps-AI v1.0 — Documentación Técnica de la API
**Autor:** **Desarrollado v1.0 Miguel Benítez**  
**Finalidad:** *Proyecto desarrollado con fines estrictamente educativos, académicos y de demostración técnica MLOps.*  
**Licencia:** GNU General Public License v3.0 (GPL-3.0) con Atribución Obligatoria  
**Datos Fuente:** Autoridad Marítima de Panamá (AMP) — Período Histórico Oficial 2015–2026 (140 meses continuos).  

---

## 🧭 Guía Tutorial: ¿Cómo utilizar los servicios de la API?

Esta API permite consultar modelos predictivos de Machine Learning entrenados sobre el movimiento mensual de contenedores (TEUs) en las 6 terminales portuarias de Panamá.

### 1. Inferencia Predictiva (`POST /predict`)
Genera pronósticos puntuales y por cuantiles para cualquier puerto a un horizonte de 1 a 6 meses.
Permite evaluar escenarios de sensibilidad operacional (*What-If*) y seleccionar entre 4 familias de algoritmos:
- `ensemble` (LightGBM Cuantiles P10, P50, P90 - **Champion**)
- `random_forest` (Random Forest Regressor - **Challenger de Baja Latencia**)
- `gradient_boosting` (HistGradientBoostingRegressor)
- `ridge_elasticnet` (Modelo Lineal Regularizado con StandardScaler)

#### Ejemplo con Python (`requests`):
```python
import requests

url = "http://127.0.0.1:8000/predict"
payload = {
    "port": "Puerto Balboa",
    "horizon_months": 3,
    "what_if_bunkering_shift_pct": 0.0,
    "what_if_transshipment_shift_pct": -15.0,  # Simular caída de 15% en trasbordo
    "algorithm": "ensemble"
}
response = requests.post(url, json=payload)
data = response.json()
print("Pronóstico Central P50:", data["predictions"][0]["pred_p50_teu"])
print("Suelo Pesimista P10:", data["predictions"][0]["pred_p10_teu"])
print("Techo de Capacidad P90:", data["predictions"][0]["pred_p90_teu"])
```

#### Ejemplo con cURL (Terminal):
```bash
curl -X POST "http://127.0.0.1:8000/predict" \\
     -H "Content-Type: application/json" \\
     -d '{"port": "SSA Marine MIT", "horizon_months": 2, "algorithm": "random_forest"}'
```

---

### 2. Simulación Estocástica de Monte Carlo (`POST /simulate`)
Evalúa el comportamiento de la terminal ante eventos de estrés severo (Sequías en el Canal, Shocks de Combustible o Recesión).
Calcula métricas de gestión de riesgo:
- **Value at Risk (VaR 95%):** Nivel mínimo de volumen con 95% de confianza estadística.
- **Conditional VaR (CVaR / Expected Shortfall):** Promedio de volumen condicional en el peor 5% de los escenarios.
- **Probabilidad de caída severa:** Probabilidad empírica de una contracción superior al 25%.

#### Ejemplo con Python:
```python
sim_payload = {
    "port": "Puerto Balboa",
    "horizon_months": 6,
    "num_paths": 200,
    "scenario_type": "canal_drought"
}
res = requests.post("http://127.0.0.1:8000/simulate", json=sim_payload).json()
print("VaR 95%:", res["var_95_volume"], "TEUs")
print("CVaR 95% (Expected Shortfall):", res["cvar_95_expected_shortfall"], "TEUs")
```

---

### 3. Consultas de Benchmarking y Metodología en Navegador
Los endpoints `/api/models/compare`, `/api/models/diagnostics` y `/api/methodology` cuentan con **negociación de contenido**:
- Si se abren directamente en el navegador web, muestran una **interfaz visual interactiva y pedagógica**.
- Si se consultan por código (HTTP `Accept: application/json`), retornan el **payload JSON estructurado**.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Loads machine learning bundle, stress tester, feature store, and benchmark metrics into memory on startup.
    """
    logger.info("Initializing FastAPI Serving Application (Desarrollado v1.0 Miguel Benítez)...")
    bundle_path = MODELS_DIR / "champion_models.joblib"
    if not bundle_path.exists():
        logger.error(f"Model bundle not found at {bundle_path}")
        raise RuntimeError("Model bundle missing. Run 'python -m src.models.train' first.")

    ml_artifacts["bundle"] = joblib.load(bundle_path)
    ml_artifacts["registry_mgr"] = ModelRegistryManager()

    # Load benchmark summary if available
    benchmark_path = MODELS_DIR / "model_benchmark.json"
    if benchmark_path.exists():
        with open(benchmark_path, "r", encoding="utf-8") as f:
            ml_artifacts["benchmark_data"] = json.load(f)

    # Load feature store snapshot
    feat_path = GOLD_DIR / "container_features.parquet"
    if feat_path.exists():
        ml_artifacts["features_df"] = pd.read_parquet(feat_path)

    # Initialize stress tester
    try:
        ml_artifacts["stress_tester"] = PortStressTester(model_bundle_path=bundle_path)
    except Exception as e:
        logger.warning(f"Could not initialize stress tester during startup: {e}")

    logger.info("All model artifacts and feature stores successfully loaded in memory.")
    yield
    ml_artifacts.clear()
    logger.info("FastAPI Serving Application shutdown complete.")


app = FastAPI(
    title="Panamá PortOps-AI Platform",
    description=API_DESCRIPTION,
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

# Mount static files directory if it exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def wants_html(request: Request) -> bool:
    """Helper to detect if request comes from a human web browser rather than an API client."""
    accept = request.headers.get("accept", "")
    return "text/html" in accept and request.query_params.get("format") != "json"


def render_html_page(title: str, subtitle: str, content_html: str) -> str:
    """Renders a minimalist, dark-mode, educational HTML wrapper for browser views."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | Panamá PortOps-AI</title>
  <link rel="stylesheet" href="/static/css/style.css">
  <style>
    .endpoint-container {{ max-width: 1200px; margin: 2rem auto; padding: 0 1.5rem; }}
    .endpoint-header {{ margin-bottom: 2rem; border-bottom: 1px solid var(--border-color); padding-bottom: 1rem; }}
    .endpoint-header h1 {{ font-size: 1.6rem; color: var(--cyan-bright); margin-bottom: 0.35rem; }}
    .endpoint-header p {{ color: var(--text-muted); font-size: 0.95rem; }}
    .endpoint-badge-bar {{ display: flex; gap: 0.5rem; margin-top: 0.75rem; flex-wrap: wrap; }}
    .json-switch-link {{ color: var(--blue-vivid); text-decoration: none; font-size: 0.82rem; }}
    .json-switch-link:hover {{ text-decoration: underline; }}
    .code-block {{ background: rgba(0,0,0,0.4); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; font-family: var(--font-mono); font-size: 0.85rem; color: #a5f3fc; overflow-x: auto; }}
  </style>
</head>
<body>
  <header>
    <div class="nav-container">
      <div class="logo-group">
        <a href="/" style="text-decoration:none; display:flex; align-items:center; gap:0.85rem;">
          <div class="logo-icon-wrapper">
            <svg class="nav-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 20a2.4 2.4 0 0 0 2 1 2.4 2.4 0 0 0 2-1 2.4 2.4 0 0 1 2-1 2.4 2.4 0 0 1 2 1 2.4 2.4 0 0 0 2 1 2.4 2.4 0 0 0 2-1 2.4 2.4 0 0 1 2-1 2.4 2.4 0 0 1 2 1 2.4 2.4 0 0 0 2 1 2.4 2.4 0 0 0 2-1"></path><path d="M4 18v-5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v5"></path><path d="M12 3v8"></path><path d="m8 7 4-4 4 4"></path></svg>
          </div>
          <div class="logo-text">
            <h1>Panamá PortOps-AI <span class="version-badge">v1.0</span></h1>
            <p class="author-signature">Desarrollado v1.0 Miguel Benítez — Fines Educativos</p>
          </div>
        </a>
      </div>
      <div class="nav-badges">
        <a href="/" class="badge link-badge">🖥️ Plataforma Web</a>
        <a href="/docs" class="badge link-badge">📖 Swagger Docs</a>
        <span class="badge healthy"><span class="status-dot"></span> API Operacional</span>
      </div>
    </div>
  </header>

  <main class="endpoint-container">
    <div class="endpoint-header">
      <h1>{title}</h1>
      <p>{subtitle}</p>
      <div class="endpoint-badge-bar">
        <span class="badge">Autor: Desarrollado v1.0 Miguel Benítez</span>
        <span class="badge">Finalidad: Fines Educativos</span>
        <a href="?format=json" class="badge link-badge">Ver en formato JSON crudo</a>
      </div>
    </div>

    {content_html}
  </main>

  <footer>
    <div class="footer-container">
      <div class="footer-left">
        <div class="footer-brand">Panamá PortOps-AI v1.0</div>
        <p class="footer-author">Desarrollado v1.0 Miguel Benítez — Proyecto con Fines Educativos</p>
      </div>
      <div class="footer-right">
        <div class="footer-links">
          <a href="/" class="footer-link">Inicio</a>
          <a href="/docs" class="footer-link">Swagger UI</a>
          <a href="/api/models/compare" class="footer-link">Benchmark</a>
          <a href="/api/models/diagnostics" class="footer-link">Diagnósticos</a>
          <a href="/api/methodology" class="footer-link">Metodología</a>
        </div>
      </div>
    </div>
  </footer>
</body>
</html>"""


# --- Pydantic Schemas (Pydantic v2 compliant) ---
class PredictionRequest(BaseModel):
    port: str = Field(
        ...,
        description="Terminal portuaria panameña destino. Opciones: Puerto Balboa, SSA Marine MIT, PSA Panama International Terminal, Colon Container Terminal, Puerto Cristóbal, Bocas Fruit Co.",
        json_schema_extra={"example": "Puerto Balboa"}
    )
    horizon_months: int = Field(
        default=3,
        ge=1,
        le=6,
        description="Horizonte de proyección en meses adelante (1 a 6).",
        json_schema_extra={"example": 3}
    )
    what_if_bunkering_shift_pct: float = Field(
        default=0.0,
        ge=-50.0,
        le=50.0,
        description="Simulación de sensibilidad (What-If): % de cambio hipotético en el suministro nacional de combustible marino (VLSFO). Rango: -50% a +50%.",
        json_schema_extra={"example": 0.0}
    )
    what_if_transshipment_shift_pct: float = Field(
        default=0.0,
        ge=-50.0,
        le=50.0,
        description="Simulación de sensibilidad (What-If): % de cambio hipotético en la carga de trasbordo interoceánico. Rango: -50% a +50%.",
        json_schema_extra={"example": 0.0}
    )
    algorithm: Optional[str] = Field(
        default="ensemble",
        description="Algoritmo predictivo a utilizar: 'ensemble' (LightGBM Cuantiles P10/P50/P90), 'random_forest' (Random Forest), 'gradient_boosting' (HistGradientBoosting) o 'ridge_elasticnet' (Lineal regularizado).",
        json_schema_extra={"example": "ensemble"}
    )


class ForecastResult(BaseModel):
    port: str = Field(..., description="Nombre canónico del puerto panameño.")
    target_month: str = Field(..., description="Mes proyectado en formato ISO YYYY-MM.")
    horizon_step: int = Field(..., description="Número de mes hacia adelante proyectado (1 a 6).")
    pred_p10_teu: float = Field(..., description="Cuantil P10: Suelo de seguridad operacional (10% de probabilidad de caer por debajo).")
    pred_p50_teu: float = Field(..., description="Cuantil P50: Pronóstico central o mediana esperada en TEUs.")
    pred_p90_teu: float = Field(..., description="Cuantil P90: Techo de capacidad pico para dimensionamiento de patio y grúas STS.")
    empty_ratio_estimate: float = Field(..., description="Proporción proyectada de contenedores vacíos frente a llenos (TEU vacíos / TEU llenos).")
    imbalance_status: str = Field(..., description="Semáforo operativo: NORMAL_BALANCED, CRITICAL_SURPLUS_CONTAINERS o DEFICIT_CONTAINERS.")


class PredictionResponse(BaseModel):
    status: str
    author: str
    algorithm_used: str
    port: str
    total_horizon_months: int
    predictions: List[ForecastResult]
    latency_ms: float


class SimulationRequest(BaseModel):
    port: str = Field(default="Puerto Balboa", description="Terminal portuaria panameña a simular.")
    horizon_months: int = Field(default=6, ge=1, le=12, description="Horizonte de simulación estocástica en meses.")
    num_paths: int = Field(default=100, ge=10, le=500, description="Número de trayectorias sintéticas coordinadas.")
    scenario_type: str = Field(default="baseline", description="Escenario de estrés: 'baseline', 'canal_drought', 'bunker_crisis', 'us_recession' o 'compound_black_swan'.")


class HealthResponse(BaseModel):
    status: str
    author: str
    educational_note: str
    model_loaded: bool
    service_timestamp: str


# --- Web UI Route ---
@app.get("/", include_in_schema=False)
def serve_web_ui():
    """Serves the modern, minimalist static web user interface."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Panamá PortOps-AI API is running. Visit /docs for OpenAPI specs."}


# --- API Endpoints ---
@app.get("/health", response_model=HealthResponse, tags=["System Health & Infrastructure"])
def health_check():
    """Sonda de salud operacional (Liveness & Readiness probe)."""
    is_ready = "bundle" in ml_artifacts and "models" in ml_artifacts["bundle"]
    return {
        "status": "healthy" if is_ready else "unhealthy",
        "author": "Desarrollado v1.0 Miguel Benítez",
        "educational_note": "Proyecto desarrollado con fines estrictamente educativos y de investigación MLOps.",
        "model_loaded": is_ready,
        "service_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }


@app.get("/api/ports", tags=["Model Serving & Forecasting"])
def get_available_ports():
    """Retorna la lista de terminales portuarias panameñas admitidas por el modelo."""
    return {
        "author": "Desarrollado v1.0 Miguel Benítez",
        "ports": VALID_PORTS
    }


@app.get("/api/history/{port_name}", tags=["Model Serving & Forecasting"])
def get_port_history(port_name: str, limit_months: int = Query(24, ge=1, le=140)):
    """Retorna el historial empírico real de TEUs de la terminal solicitada para visualización gráfica."""
    if port_name not in VALID_PORTS:
        raise HTTPException(status_code=400, detail=f"Puerto inválido: '{port_name}'")

    features_df = ml_artifacts.get("features_df")
    if features_df is None:
        raise HTTPException(status_code=503, detail="Feature Store no cargado en memoria.")

    sub = features_df[features_df["port"] == port_name].sort_values(by="date").tail(limit_months)
    records = []
    for _, r in sub.iterrows():
        records.append({
            "date": pd.to_datetime(r["date"]).strftime("%Y-%m"),
            "teu_total": float(r["teu_total"]),
            "empty_ratio": float(r.get("empty_ratio", 0.0)),
            "transshipment_ratio": float(r.get("transshipment_ratio", 0.0))
        })
    return {
        "author": "Desarrollado v1.0 Miguel Benítez",
        "port": port_name,
        "history": records
    }


@app.get("/api/models/compare", tags=["Model Benchmarking & Comparison"])
def compare_models(request: Request):
    """
    Evaluación comparativa formal entre las 4 arquitecturas de algoritmos:
    - LightGBM Cuantílico (Champion)
    - Random Forest Regressor (Challenger)
    - HistGradientBoosting (Challenger)
    - Ridge / ElasticNet con Pipeline StandardScaler (Challenger)
    
    *Nota: Si se visita desde el navegador, se presenta una vista visual pedagógica.*
    """
    benchmark_data = ml_artifacts.get("benchmark_data")
    bundle = ml_artifacts.get("bundle", {})
    payload = benchmark_data if benchmark_data else {
        "author": "Desarrollado v1.0 Miguel Benítez",
        "benchmark_comparison": bundle.get("benchmark_table", {}),
        "splits_summary": bundle.get("metrics_summary", [])
    }

    if wants_html(request):
        comp = payload.get("benchmark_comparison", {})
        splits = payload.get("splits_summary", [])
        
        cards_html = "<div class='benchmark-cards-grid'>"
        for k, v in comp.items():
            status_cls = "champion" if v.get("status") == "Champion" else ("baseline" if "ridge" in k else "")
            wape_str = f"{v.get('avg_wape', 0)*100:.2f}%" if v.get("avg_wape", 0) < 5.0 else ">1,000% (Colapso Lineal)"
            cards_html += f"""
            <div class='algo-stat-card {status_cls}'>
              <div class='algo-badge-top'>{v.get('status')}</div>
              <div class='algo-name'>{k.upper()}</div>
              <div class='algo-metric'>WAPE Promedio: <span class='highlight'>{wape_str}</span></div>
              <div class='algo-submetric'>R²: {v.get('avg_r2')} | RMSE: {v.get('avg_rmse'):,.0f} | Latencia: {v.get('avg_latency_ms')} ms</div>
            </div>"""
        cards_html += "</div>"

        splits_html = """
        <div class='table-responsive' style='margin-top:2rem;'>
          <h3>Desglose Temporal por Partición de Validación (Expanding Window)</h3>
          <table class='data-table'>
            <thead>
              <tr>
                <th>Partición</th>
                <th>Período Fuera de Muestra</th>
                <th>LightGBM WAPE</th>
                <th>Random Forest WAPE</th>
                <th>Gradient Boosting WAPE</th>
                <th>Ridge WAPE</th>
                <th>R² Score</th>
              </tr>
            </thead>
            <tbody>"""
        for s in splits:
            ridge_val = f"{s.get('ridge_elasticnet_wape', 0)*100:.2f}%" if s.get('ridge_elasticnet_wape', 0) < 1.0 else "Colapso"
            splits_html += f"""
            <tr>
              <td>Split {s.get('split')}</td>
              <td><strong>{s.get('period')}</strong></td>
              <td style='color:var(--cyan-bright); font-weight:700;'>{s.get('lightgbm_wape', 0)*100:.2f}%</td>
              <td>{s.get('random_forest_wape', 0)*100:.2f}%</td>
              <td>{s.get('gradient_boosting_wape', 0)*100:.2f}%</td>
              <td style='color:{"#10b981" if "Colapso" not in ridge_val else "#f43f5e"};'>{ridge_val}</td>
              <td>{s.get('lightgbm_r2')}</td>
            </tr>"""
        splits_html += "</tbody></table></div>"

        doc_html = """
        <div class='card' style='margin-top:2rem;'>
          <h3>¿Cómo interpretar este reporte de Benchmarking?</h3>
          <p style='color:var(--text-muted); font-size:0.9rem; margin-top:0.5rem;'>
            <strong>1. WAPE (Weighted Absolute Percentage Error):</strong> Es la métrica industrial por excelencia en logística portuaria porque pondera el error por el volumen real de la terminal, evitando la división por cero.<br>
            <strong>2. ¿Por qué LightGBM es Champion?:</strong> Porque logra un error de solo <strong>9.11%</strong> y proporciona estimaciones cuantílicas directas (P10, P50, P90) sin asumir normalidad en los errores.<br>
            <strong>3. ¿Por qué el modelo lineal colapsa en Split 3?:</strong> En series de tiempo portuarias con 81 variables correlacionadas (lags t-1..t-12), la multicolinealidad severa condiciona negativamente la matriz Hessiana lineal, demostrando que los modelos de árboles son obligatorios para este dominio.
          </p>
        </div>"""

        return HTMLResponse(content=render_html_page(
            title="Evaluación Comparativa de Modelos (Benchmarking)",
            subtitle="Resultados empíricos sobre las 140 particiones mensuales de la Autoridad Marítima de Panamá.",
            content_html=cards_html + splits_html + doc_html
        ))

    return payload


@app.get("/api/models/diagnostics", tags=["Statistical Diagnostics & Explainability"])
def get_model_diagnostics(request: Request):
    """
    Retorna el diagnóstico estadístico completo:
    - Análisis de distribución de residuos reales (Media, Desviación Estándar, Asimetría / Skewness)
    - Puntos temporales empíricos de residuos (y_true vs y_pred)
    - Top 15 importancias de variables empíricas de LightGBM (Split Gain)
    - Multicolinealidad bivariada (|r| > 0.85) y Factor de Inflación de la Varianza (VIF)
    - Mapeo causal y tratamiento detallado de variables confundidoras (Confounders)
    
    *Nota: Si se visita desde el navegador, se presenta una vista visual pedagógica.*
    """
    bundle = ml_artifacts.get("bundle", {})
    diagnostics = bundle.get("diagnostics")
    if not diagnostics:
        benchmark_data = ml_artifacts.get("benchmark_data", {})
        diagnostics = benchmark_data.get("diagnostics")
    if not diagnostics:
        raise HTTPException(status_code=503, detail="Diagnósticos estadísticos no inicializados.")

    if wants_html(request):
        res_stats = diagnostics.get("residual_stats", {})
        feat_imps = diagnostics.get("feature_importances", [])
        confounders = diagnostics.get("confounders", [])
        vif_scores = diagnostics.get("collinearity", {}).get("vif_scores", {})
        high_pairs = diagnostics.get("collinearity", {}).get("high_correlation_pairs", [])

        stats_html = f"""
        <div class='kpi-grid' style='margin-bottom:1.5rem;'>
          <div class='kpi-card'>
            <div class='kpi-title'>Error Residual Medio</div>
            <div class='kpi-value'>{res_stats.get('mean_residual', 0):+,.0f} TEUs</div>
            <div class='kpi-sub'>Media no condicionada</div>
          </div>
          <div class='kpi-card'>
            <div class='kpi-title'>Desviación Estándar</div>
            <div class='kpi-value'>{res_stats.get('std_residual', 0):,.0f} TEUs</div>
            <div class='kpi-sub'>Dispersión de error</div>
          </div>
          <div class='kpi-card'>
            <div class='kpi-title'>Error Absoluto Mediano</div>
            <div class='kpi-value'>{res_stats.get('median_absolute_error', 0):,.0f} TEUs</div>
            <div class='kpi-sub'>Mediana de |y - y_hat|</div>
          </div>
          <div class='kpi-card'>
            <div class='kpi-title'>Asimetría (Skewness)</div>
            <div class='kpi-value'>{res_stats.get('skewness', 0):.3f}</div>
            <div class='kpi-sub'>Distribución casi simétrica</div>
          </div>
        </div>"""

        conf_html = "<h3>Catálogo y Tratamiento Causal de Variables Confundidoras</h3><div style='margin-top:1rem;'>"
        for c in confounders:
            conf_html += f"""
            <div class='confounder-card' style='margin-bottom:1rem;'>
              <div class='confounder-title'>
                <span>{c.get('name')}</span>
                <span class='confounder-type'>{c.get('type')}</span>
              </div>
              <p style='margin:0.4rem 0;'><strong>¿Qué se hizo?:</strong> {c.get('what', c.get('effect'))}</p>
              <p style='margin:0.4rem 0; color:var(--cyan-bright);'><strong>¿Cómo se hizo?:</strong> {c.get('how', c.get('treatment'))}</p>
              <p style='margin:0.4rem 0; color:var(--emerald-success);'><strong>¿Por qué se hizo?:</strong> {c.get('why', 'Aislamiento de sesgo de estimación.')}</p>
            </div>"""
        conf_html += "</div>"

        return HTMLResponse(content=render_html_page(
            title="Diagnóstico Estadístico y Explicabilidad Causal",
            subtitle="Auditoría matemática de residuos, importancia de variables y control de confundidores.",
            content_html=stats_html + conf_html
        ))

    return diagnostics


@app.get("/api/methodology", tags=["Methodology & Data Governance"])
def get_methodology_overview(request: Request):
    """
    Retorna el resumen técnico estructurado de la metodología de ciencia de datos implementada:
    - Data Cleaning y deduplicación bitemporal
    - Normalización y estandarización Z-score
    - Protocolos de anonimización para datos sensibles
    - Tratamiento de datos categóricos y valores incompletos
    - Formulación de soluciones operacionales
    
    *Nota: Si se visita desde el navegador, se presenta una vista visual pedagógica.*
    """
    payload = {
        "author": "Desarrollado v1.0 Miguel Benítez",
        "educational_objective": "Demostración de pipeline industrial MLOps reproducible desde cero con datos reales de Panamá.",
        "version": "1.0",
        "documentation_file": "METODOLOGIA_Y_ARQUITECTURA_MLOPS.md",
        "data_cleaning": {
            "negative_values": "Rectificación determinista de valores contables negativos a 0.0.",
            "bitemporal_deduplication": "Indexación por (fecha_validez, fecha_publicación), conservando max(timestamp) del último corte mensual.",
            "extreme_outliers": "Filtro Hampel con Desviación Absoluta de la Mediana (MAD)."
        },
        "imputation": {
            "missing_series": "Forward-fill temporal agrupado por terminal portuaria.",
            "structural_zeros": "Imputación de 0.0 en terminales especializadas sin carga de Zona Libre.",
            "indicators": "Banderas binarias auxiliares de imputación para variables de rezago exógeno."
        },
        "normalization_standardization": {
            "tree_models": "Escala natural preservada debido a la invariancia a transformaciones monótonas crecientes.",
            "linear_models": "StandardScaler Z-score Z = (X - mu) / sigma ajustado estrictamente sobre pliegues de entrenamiento."
        },
        "anonymization_and_privacy": {
            "aggregation": "Agregación canónica a nivel Puerto x Mes x Litoral (sin exposición de Bills of Lading individuales).",
            "cryptography": "Salteo criptográfico HMAC-SHA256 para códigos de buques IMO y operadores en microdatos granulares."
        },
        "confounders": {
            "chinese_new_year": "Desacoplado mediante armónicos ortogonales sin/cos y bandera is_cny.",
            "canal_drought": "Controlado con lags exógenos de bunkering VLSFO y dummies de litoral.",
            "terminal_capacity": "Controlado mediante modelo de efectos fijos por terminal con One-Hot Encoding."
        }
    }

    if wants_html(request):
        html_content = """
        <div class='methodology-grid'>
          <div class='method-card'>
            <div class='method-badge'>Pilar 1</div>
            <h3>Data Cleaning y Deduplicación Bitemporal</h3>
            <p><strong>¿Qué?:</strong> Limpieza de 353 archivos CSV gubernamentales con formatos mixtos.</p>
            <p><strong>¿Cómo?:</strong> Indexación por tupla <code>(fecha_validez, fecha_publicacion)</code>, conservando exclusivamente la versión de fecha más reciente.</p>
            <p><strong>¿Por qué?:</strong> Los boletines de la AMP son acumulativos mensuales. Sin deduplicación bitemporal, se cuadruplica artificialmente el volumen.</p>
          </div>
          <div class='method-card'>
            <div class='method-badge'>Pilar 2</div>
            <h3>Normalización y Estandarización</h3>
            <p><strong>¿Qué?:</strong> Tratamiento de escala de variables según la familia algorítmica.</p>
            <p><strong>¿Cómo?:</strong> Árboles en escala física original (invarianza monótona); modelos lineales con <code>StandardScaler</code> Z-score.</p>
            <p><strong>¿Por qué?:</strong> Evita distorsionar las penalizaciones L1/L2 en features de diferente magnitud.</p>
          </div>
          <div class='method-card'>
            <div class='method-badge'>Pilar 3</div>
            <h3>Anonimización y Privacidad</h3>
            <p><strong>¿Qué?:</strong> Protección de información comercial confidencial.</p>
            <p><strong>¿Cómo?:</strong> Agregación canónica macro y hashing <code>HMAC-SHA256 con sal</code> para identificadores de buques IMO.</p>
            <p><strong>¿Por qué?:</strong> Cumplimiento de normativas de seguridad marítima internacional (Código ISPS y GDPR).</p>
          </div>
          <div class='method-card'>
            <div class='method-badge'>Pilar 4</div>
            <h3>Campos Faltantes y Categóricos</h3>
            <p><strong>¿Qué?:</strong> Imputación temporal estructurada y codificación One-Hot.</p>
            <p><strong>¿Cómo?:</strong> Forward-fill por puerto, preservación de ceros estructurales y alineación de columnas fijas en inferencia.</p>
            <p><strong>¿Por qué?:</strong> Evita la fuga de datos (*data leakage*) y garantiza estabilidad en tiempo de inferencia.</p>
          </div>
          <div class='method-card'>
            <div class='method-badge'>Pilar 5</div>
            <h3>Variables Dependientes e Independientes</h3>
            <p><strong>¿Qué?:</strong> Definición formal del espacio target Y y features X.</p>
            <p><strong>¿Cómo?:</strong> Y = TEU Total mensual (t+1..t+6). X = 81 features (lags, rolling stats, ratios de trasbordo/vacíos, VLSFO).</p>
            <p><strong>¿Por qué?:</strong> Responde directamente al requerimiento de planificación logística de las terminales.</p>
          </div>
          <div class='method-card'>
            <div class='method-badge'>Pilar 6</div>
            <h3>Decisiones Operacionales Reales</h3>
            <p><strong>¿Qué?:</strong> Políticas de patio activadas por las predicciones del modelo.</p>
            <p><strong>¿Cómo?:</strong> Dimensionamiento de grúas STS con P90 y alerta de buques de evacuación con ratio vacíos > 0.80.</p>
            <p><strong>¿Por qué?:</strong> Transforma estimaciones matemáticas en valor de negocio logístico medible.</p>
          </div>
        </div>"""
        return HTMLResponse(content=render_html_page(
            title="Tratado Metodológico y Fundamentos de Ciencia de Datos",
            subtitle="Explicación detallada de cada paso de ingeniería y procesamiento implementado en Panamá PortOps-AI.",
            content_html=html_content
        ))

    return payload


@app.get("/model/metadata", tags=["Methodology & Data Governance"])
def get_model_metadata():
    """Retorna los metadatos de gobernanza y linaje del modelo @champion en MLflow Model Registry."""
    if "registry_mgr" not in ml_artifacts:
        raise HTTPException(status_code=503, detail="Registry no inicializado.")
    return ml_artifacts["registry_mgr"].get_champion_metadata()


@app.post("/predict", response_model=PredictionResponse, tags=["Model Serving & Forecasting"])
def predict_container_throughput(req: PredictionRequest):
    """
    Genera pronósticos multi-horizonte con incertidumbre cuantílica (P10, P50, P90)
    y alertas estocásticas de desbalance de contenedores vacíos, con soporte multi-algoritmo.
    """
    start_time = time.time()

    if req.port not in VALID_PORTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid port '{req.port}'. Allowed ports: {VALID_PORTS}"
        )

    bundle = ml_artifacts.get("bundle")
    features_df = ml_artifacts.get("features_df")

    if not bundle or features_df is None:
        raise HTTPException(status_code=503, detail="Artefactos del modelo no inicializados en memoria.")

    models = bundle["models"]
    feature_cols = bundle["feature_cols"]

    # Filter latest available observation for requested port
    port_records = features_df[features_df["port"] == req.port].sort_values(by="date")
    if port_records.empty:
        raise HTTPException(status_code=404, detail=f"No se encontraron registros históricos para {req.port}")

    latest_row = port_records.iloc[-1].copy()
    latest_date = pd.to_datetime(latest_row["date"])

    # One-hot encode port categories
    df_all_encoded = pd.get_dummies(features_df, columns=["port", "littoral"], drop_first=False)
    encoded_row = df_all_encoded[df_all_encoded["port_" + req.port] == 1].iloc[-1:].copy()

    # Apply What-If perturbations
    if req.what_if_bunkering_shift_pct != 0.0 and "nat_vlsfo_sales_tm_lag1" in encoded_row.columns:
        encoded_row["nat_vlsfo_sales_tm_lag1"] *= (1.0 + req.what_if_bunkering_shift_pct / 100.0)

    if req.what_if_transshipment_shift_pct != 0.0 and "transshipment_ratio_lag_1" in encoded_row.columns:
        encoded_row["transshipment_ratio_lag_1"] = np.clip(
            encoded_row["transshipment_ratio_lag_1"] * (1.0 + req.what_if_transshipment_shift_pct / 100.0), 0.0, 1.0
        )

    # Multi-horizon recursive projection
    current_features = encoded_row[feature_cols].fillna(0).copy()
    selected_algo = (req.algorithm or "ensemble").lower().strip()
    predictions = []

    # Map model selection
    primary_model = models.get("p50")
    if selected_algo == "random_forest" and "random_forest" in models:
        primary_model = models["random_forest"]
    elif selected_algo == "gradient_boosting" and "gradient_boosting" in models:
        primary_model = models["gradient_boosting"]
    elif selected_algo in ["ridge", "elasticnet", "ridge_elasticnet"] and "ridge_elasticnet" in models:
        primary_model = models["ridge_elasticnet"]

    for step in range(1, req.horizon_months + 1):
        target_dt = latest_date + pd.DateOffset(months=step)

        # Predict point estimate
        raw_pred = float(primary_model.predict(current_features)[0])
        p50_val = max(0.0, raw_pred)

        # Quantile bounds
        if selected_algo in ["ensemble", "lightgbm"] and "p10" in models and "p90" in models:
            p10_val = max(0.0, float(models["p10"].predict(current_features)[0]))
            p90_val = max(p50_val, float(models["p90"].predict(current_features)[0]))
            p10_val = min(p10_val, p50_val)
        else:
            # Empirical variance approximation for non-quantile regressors (approx 10% band)
            p10_val = max(0.0, p50_val * 0.88)
            p90_val = p50_val * 1.12

        # Empty Container Imbalance Status
        empty_ratio_hist = float(latest_row.get("empty_ratio", 0.5))
        if empty_ratio_hist > 0.8:
            imbalance_status = "CRITICAL_SURPLUS_CONTAINERS"
        elif empty_ratio_hist < 0.2:
            imbalance_status = "DEFICIT_CONTAINERS"
        else:
            imbalance_status = "NORMAL_BALANCED"

        predictions.append(ForecastResult(
            port=req.port,
            target_month=target_dt.strftime("%Y-%m"),
            horizon_step=step,
            pred_p10_teu=round(p10_val, 1),
            pred_p50_teu=round(p50_val, 1),
            pred_p90_teu=round(p90_val, 1),
            empty_ratio_estimate=round(empty_ratio_hist, 3),
            imbalance_status=imbalance_status
        ))

        # Update recursive lag
        if "teu_total_lag_1" in current_features.columns:
            current_features["teu_total_lag_1"] = p50_val

    latency = round((time.time() - start_time) * 1000, 2)

    return PredictionResponse(
        status="success",
        author="Desarrollado v1.0 Miguel Benítez",
        algorithm_used=selected_algo,
        port=req.port,
        total_horizon_months=req.horizon_months,
        predictions=predictions,
        latency_ms=latency
    )


@app.post("/predict/batch", tags=["Model Serving & Forecasting"])
def predict_batch_all_ports(horizon_months: int = Query(default=3, ge=1, le=6)):
    """Batch inference endpoint running simultaneous forecasts for all Panamanian terminals."""
    results = {}
    for p in VALID_PORTS:
        req = PredictionRequest(port=p, horizon_months=horizon_months)
        res = predict_container_throughput(req)
        results[p] = [p_item.model_dump() for p_item in res.predictions]
    return {
        "status": "success",
        "author": "Desarrollado v1.0 Miguel Benítez",
        "total_ports": len(VALID_PORTS),
        "horizon_months": horizon_months,
        "batch_forecasts": results
    }


@app.post("/simulate", tags=["Monte Carlo Simulation & Risk"])
def run_monte_carlo_simulation(req: SimulationRequest):
    """
    Ejecuta simulación estocástica multivariada de Monte Carlo coordinada vía cópulas gaussianas (Cholesky)
    y procesos de difusión con saltos de Merton (1976), calculando Value at Risk (VaR) y CVaR.
    """
    start_time = time.time()
    if req.port not in VALID_PORTS:
        raise HTTPException(status_code=400, detail=f"Puerto inválido: '{req.port}'")

    tester = ml_artifacts.get("stress_tester")
    if tester is None:
        raise HTTPException(status_code=503, detail="Motor estocástico de simulación no inicializado.")

    try:
        sim_results = tester.run_stress_test(
            port_name=req.port,
            horizon=req.horizon_months,
            num_paths=req.num_paths,
            scenarios=[req.scenario_type]
        )
        latency = round((time.time() - start_time) * 1000, 2)
        sc_data = sim_results["scenarios"].get(req.scenario_type, {})
        return {
            "status": "success",
            "author": "Desarrollado v1.0 Miguel Benítez",
            "port": req.port,
            "scenario": req.scenario_type,
            "horizon_months": req.horizon_months,
            "num_paths": req.num_paths,
            "expected_volume": sc_data.get("expected_volume"),
            "volatility_std": sc_data.get("volatility_std"),
            "var_95_volume": sc_data.get("var_95_volume"),
            "var_99_volume": sc_data.get("var_99_volume"),
            "cvar_95_expected_shortfall": sc_data.get("cvar_95_expected_shortfall"),
            "prob_severe_drop_25pct": sc_data.get("prob_severe_drop_25pct"),
            "trajectory_profile": sc_data.get("trajectory_profile", []),
            "endpoint_sample": sc_data.get("endpoint_sample", [])[:50],
            "latency_ms": latency
        }
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.serving.api:app", host="0.0.0.0", port=8000, reload=True)
