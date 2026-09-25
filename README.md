# Panamá PortOps-AI v1.0 — Plataforma Industrial MLOps Portuaria y Simulación Estocástica

> **AVISO IMPORTANTE:**  
> **Este proyecto ha sido desarrollado con fines estrictamente educativos, pedagógicos, académicos y de demostración técnica en ingeniería MLOps.** Constituye un ejemplo integral de cómo diseñar, estructurar, entrenar, auditar y servir modelos predictivos y estocásticos en producción desde cero, utilizando datos 100% empíricos de la **Autoridad Marítima de Panamá (AMP)** correspondientes a 140 meses continuos (2015–2026).
>
> **Autor Principal:** **Miguel Benítez** (`mbeni`)  
> **Firma Oficial:** **`Desarrollado v1.0 Miguel Benítez`**  
> **Licencia:** GNU General Public License v3.0 (GPL-3.0) con Atribución Obligatoria (Sección 7)  

---

## 📌 Propósito y Alcance Educativo

El objetivo pedagógico de este repositorio es servir como **guía maestra de referencia técnica** para estudiantes, científicos de datos, ingenieros de machine learning y profesionales de la logística marítima interesados en implementar un ecosistema real de MLOps sin dependencias propietarias:

1. **Ingesta y Clasificación Taxonómica (Bronze):** Descarga, indexación y clasificación morfológica automática de 353 datasets gubernamentales heterogéneos.
2. **Deduplicación Bitemporal (Silver Parquet):** Tratamiento determinista de boletines mensuales acumulativos mediante marcas de corte `(fecha_validez, fecha_publicación)`, resolviendo la duplicación sin pérdida de historia.
3. **Control de Calidad Pre-ML (Data Quality Gates):** Barreras de validación en 5 dimensiones (completitud, unicidad, dominio canónico de puertos, continuidad y no-negatividad física).
4. **Feature Store con Cero Fuga Temporal (Gold):** Construcción de 81 variables predictivas: armónicos estacionales ($\sin/\cos$), indicadores del Año Nuevo Chino (`is_cny`), ratios marítimos (trasbordo, vacíos/llenos, TEU/unidad) y rezagos autorregresivos calculados sobre `.shift(1)`.
5. **Benchmarking Multi-Algoritmo:** Comparación empírica bajo *Expanding Window Backtesting* entre:
   - **LightGBM Quantiles (P10, P50, P90 - Champion):** WAPE 9.11%, $R^2 = 0.9594$.
   - **Random Forest Regressor (Challenger):** WAPE 9.10%, latencia ultrarrápida 4.58 ms.
   - **HistGradientBoosting (Challenger):** WAPE 9.78%.
   - **Ridge / ElasticNet con StandardScaler (Baseline):** Demostración del colapso lineal ante multicolinealidad.
6. **Diagnóstico Estadístico y Causalidad (Zero Mocks):** Análisis de residuos reales, VIF (Factor de Inflación de la Varianza) y tratamiento de variables confundidoras (*Confounders*).
7. **Motor Estocástico de Monte Carlo y Pruebas de Estrés:** Simulación con cópulas gaussianas (factorización de Cholesky $L L^T = R$), procesos de saltos de Poisson de Merton (1976), cálculo de **Value at Risk (VaR 95%)** y **Expected Shortfall (CVaR 95%)**.
8. **Microservicio REST y Frontend Web Vanguardista:** Servidor FastAPI con OpenAPI enriquecido y SPA interactiva moderna con iconografía SVG nativa y modales explicativos "¿Qué se hizo, Cómo y Por Qué?".

---

## 🏗️ Arquitectura Modular del Repositorio

```text
amp-cont-ai/
├── configs/
│   └── config.yaml                     # Rutas canónicas y parámetros de calidad
├── data/
│   ├── raw/                            # Capa Bronze: 353 CSVs oficiales descargados
│   ├── metadata/                       # Catálogos de datasets, matrices Cholesky y distribuciones
│   ├── silver/                         # Capa Silver: Fact tables normalizadas en Apache Parquet
│   │   ├── fact_containers.parquet     # 8,986 registros atómicos de contenedores (2015-2026)
│   │   ├── fact_bunkering.parquet      # 2,267 registros de despacho de combustible marino
│   │   ├── fact_roro.parquet           # 1,256 registros de vehículos y carga rodante
│   │   └── fact_port_macro.parquet     # 770 registros de indicadores macroeconómicos
│   └── gold/                           # Capa Gold: Feature Store para Machine Learning
│       ├── container_features.parquet  # 840 filas x 85 features predictivas sin fuga
│       └── bunkering_features.parquet  # 316 filas x 81 features predictivas
├── src/
│   ├── data/
│   │   ├── classifier.py               # Motor de taxonomía y clasificación contextual
│   │   ├── normalizer.py               # Deduplicador bitemporal y transformador Parquet
│   │   └── quality.py                  # Barreras de validación de calidad de datos pre-ML
│   ├── features/
│   │   ├── temporal.py                 # Armónicos cíclicos sin/cos y efecto Año Nuevo Chino
│   │   ├── maritime_ratios.py          # Ratios de trasbordo, vacíos/llenos y factor TEU/unidad
│   │   ├── lags_rolling.py             # Rezagos autorregresivos, ventanas rodantes y EWMA
│   │   └── feature_store.py            # Orquestador del Feature Store Gold
│   ├── models/
│   │   ├── train.py                    # Expanding Window Backtesting multi-algoritmo con MLflow
│   │   └── registry.py                 # Gobernanza y promoción Champion/Challenger en Registry
│   ├── simulation/
│   │   ├── distribution_profiler.py    # Ajuste MLE, prueba KS y factorización de Cholesky
│   │   ├── monte_carlo_engine.py       # Cópulas gaussianas y difusión con saltos de Merton
│   │   └── stress_tester.py            # Evaluador VaR, CVaR y Reverse Stress Testing
│   ├── serving/
│   │   ├── api.py                      # Microservicio FastAPI con Swagger educativo y vistas HTML
│   │   └── static/                     # Frontend SPA desacoplado (HTML5/CSS3/Vanilla JS)
│   │       ├── index.html              # Interfaz moderna con modales Qué, Cómo y Por Qué
│   │       ├── css/style.css           # Estilos marítimos oscuros, glassmorphism y SVGs
│   │       └── js/app.js               # Visualizaciones con Chart.js con datos 100% reales
│   ├── monitoring/
│   │   └── drift.py                    # Detección de Data Drift con Evidently AI
│   └── utils/
│       └── logger.py                   # Logger estructurado con rotación
├── tests/                              # Suite de 25 pruebas unitarias y de integración
│   ├── test_quality.py                 # Contratos de esquema y no-negatividad
│   ├── test_features.py                # Zero data leakage y armónicos estacionales
│   ├── test_model_serving.py           # Endpoints de inferencia, compare, diagnostics y batch
│   └── test_simulation.py              # Pruebas estocásticas de Cholesky, Merton y monotonía VaR
├── reports/
│   ├── DATASET_TAXONOMY_REPORT.md      # Clasificación de los 353 datasets
│   ├── EDA_AND_FEATURE_ENGINEERING.md  # Hallazgos de mercado (HHI, estacionalidad asiática)
│   ├── FEATURE_BEHAVIOR_REPORT.md      # Distribuciones paramétricas y correlaciones
│   └── MONTE_CARLO_SIMULATION_REPORT.md# Auditoría de resiliencia y Reverse Stress Testing
├── METODOLOGIA_Y_ARQUITECTURA_MLOPS.md # Tratado maestro científico de métodos y causalidad
├── DOCUMENTACION_COMPLETA_IMPLEMENTACION.md # Manual técnico integral de las 10 fases
├── AUTHORS.md                          # Atribución obligatoria a Miguel Benítez
├── LICENSE                             # GNU General Public License v3.0 con cláusula de atribución
├── CITATION.cff                        # Metadatos para citación académica
├── Makefile                            # Automatización completa de tareas
└── pyproject.toml                      # Empaquetado y configuración de pytest
```

---

## ⚡ Guía de Inicio Rápido

### 1. Requisitos Previos
- Python 3.10 o superior (recomendado 3.12).
- Sistema Operativo: Linux, macOS, Windows (PowerShell) o contenedor Docker.

### 2. Descarga de Datos Oficiales y Preparación
Dado que el repositorio excluye datasets pesados de Git por higiene y gobernanza MLOps, los datos oficiales se descargan directamente del portal del Estado panameño:
```bash
# Descarga automatizada de los datasets oficiales de la AMP (2015-2026):
make download-data
# o directamente:
python scripts/download_data.py
```

### 3. Instalación de Dependencias
```bash
pip install -r requirements.txt
# o instalar el proyecto en modo editable:
pip install -e .
```

### 4. Puesta en Marcha del Servidor y Plataforma Web
```bash
# Iniciar microservicio y frontend:
make serve
# o alternativamente:
python -m uvicorn src.serving.api:app --host 127.0.0.1 --port 8000
```
Acceso en el navegador:
- **Plataforma Web Interactiva:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Documentación Swagger UI Guiada:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Comparativa de Modelos (Vista Web):** [http://127.0.0.1:8000/api/models/compare](http://127.0.0.1:8000/api/models/compare)
- **Diagnósticos y Confundidores (Vista Web):** [http://127.0.0.1:8000/api/models/diagnostics](http://127.0.0.1:8000/api/models/diagnostics)
- **Tratado Metodológico (Vista Web):** [http://127.0.0.1:8000/api/methodology](http://127.0.0.1:8000/api/methodology)

### 5. Ejecución de la Suite de Pruebas Automatizadas (25 Tests)
```bash
make test
# o directamente con pytest:
pytest -v tests/
```

### 6. Reentrenamiento del Benchmark Multi-Algoritmo (Semilla Determinista 42)
```bash
make train
# o directamente:
python -m src.models.train
```

---

## 📚 Documentación Técnica y Tratados Maestros

Para profundizar en los fundamentos matemáticos, inferencia causal y arquitectura del proyecto:
- 📖 [`MANUAL_CIENTIFICO_MLOPS_DOCTORAL.md`](MANUAL_CIENTIFICO_MLOPS_DOCTORAL.md): **Tratado Doctoral Maestro.** Inferencia causal con DAGs de Pearl, demostración matemática de robustez MAD vs Z-Score, derivación analítica de VIF matricial, formulación Pinball loss de LightGBM, simulación de Merton, Reverse Stress Testing con optimización Powell y hoja de ruta para datos no publicados (AIS, meteorología de cuenca del Canal y fletes internacionales).
- 📖 [`METODOLOGIA_Y_ARQUITECTURA_MLOPS.md`](METODOLOGIA_Y_ARQUITECTURA_MLOPS.md): Tratado de formulación de variables $Y$ y $X$, Data Cleaning, normalización/estandarización, anonimización criptográfica, tratamiento de faltantes, VIF y variables confundidoras.
- 📖 [`DOCUMENTACION_COMPLETA_IMPLEMENTACION.md`](DOCUMENTACION_COMPLETA_IMPLEMENTACION.md): Bitácora técnica exhaustiva paso a paso de las 10 fases del proyecto.
- 📖 [`reports/MONTE_CARLO_SIMULATION_REPORT.md`](reports/MONTE_CARLO_SIMULATION_REPORT.md): Pruebas de estrés estocásticas, VaR 95%, CVaR y Reverse Stress Testing.

---

## ⚖️ Licencia y Atribución Obligatoria

Este proyecto es de código abierto bajo la licencia **GNU General Public License v3.0 (GPL-3.0)** con cláusula adicional de atribución según la Sección 7 de la licencia:

Cualquier uso educativo, investigación académica, bifurcación (*fork*) o demostración pública debe incluir obligatoriamente el siguiente reconocimiento visible:

```text
Desarrollado v1.0 Miguel Benítez
Basado en Panamá PortOps-AI por Miguel Benítez (https://github.com/miguelbenitez09/amp-cont-ai)
```

Para citar este trabajo formalmente en investigaciones o artículos:
```bibtex
@software{benitez2026portops,
  author       = {Benítez, Miguel},
  title        = {{Panamá PortOps-AI v1.0: Ecosistema MLOps, Benchmarking Multi-Algoritmo y Motor de Simulación Estocástica para Logística Portuaria}},
  year         = {2026},
  publisher    = {GitHub},
  journal      = {GitHub repository},
  howpublished = {\url{https://github.com/miguelbenitez09/amp-cont-ai}},
  note         = {Desarrollado v1.0 Miguel Benítez. Fines Educativos. Licensed under GNU GPL v3.0 with mandatory attribution}
}
```
