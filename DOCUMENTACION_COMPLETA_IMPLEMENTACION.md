# Manual Maestro de Arquitectura, Implementación y Gobernanza MLOps
## Proyecto: Panamá PortOps-AI — Plataforma de Inteligencia Portuaria y Simulación Estocástica

> **Autor:** Miguel Benítez (`miguelbenitez09`) | **Firma Oficial:** `Desarrollado v1.0 Miguel Benítez`  
> **Licencia:** GNU General Public License v3.0 (GPL-3.0) con Atribución Obligatoria (Sección 7)  
> **Datos Fuente:** Autoridad Marítima de Panamá (AMP) — Período Histórico Oficial 2015–2026  
> **Repositorio:** [Panamá PortOps-AI](https://github.com/miguelbenitez09/amp-cont-ai)  

---

## 📑 Tabla de Contenidos
1. [Diagnóstico y Resolución del Error de Conexión (`ERR_CONNECTION_REFUSED`)](#1-diagnóstico-y-resolución-del-error-de-conexión-err_connection_refused)
2. [Visión General y Propósito del Proyecto](#2-visión-general-y-propósito-del-proyecto)
3. [Arquitectura Modular del Repositorio](#3-arquitectura-modular-del-repositorio)
4. [Explicación Detallada Fase por Fase: ¿Qué se hizo, Cómo y Por Qué?](#4-explicación-detallada-fase-por-fase-qué-se-hizo-cómo-y-por-qué)
   - [Fase 1: Ingesta y Clasificación Taxonómica (Bronze)](#fase-1-ingesta-y-clasificación-taxonómica-capa-bronze)
   - [Fase 2: Normalización Bitemporal (Silver Parquet)](#fase-2-normalización-bitemporal-capa-silver-parquet)
   - [Fase 3: Puertas de Calidad de Datos (Quality Gates)](#fase-3-puertas-de-calidad-de-datos-data-quality-gates)
   - [Fase 4: Ingeniería de Características y Feature Store (Gold)](#fase-4-ingeniería-de-características-y-feature-store-capa-gold)
   - [Fase 5: Análisis Exploratorio Profundo (EDA) y Hallazgos Marítimos](#fase-5-análisis-exploratorio-de-datos-eda-y-hallazgos-marítimos)
   - [Fase 6: Entrenamiento con Backtesting y MLflow Tracking](#fase-6-entrenamiento-con-expanding-window-y-mlflow-tracking)
   - [Fase 7: Gobernanza en MLflow Model Registry](#fase-7-gobernanza-en-mlflow-model-registry)
   - [Fase 8: Observabilidad y Monitoreo de Deriva (Evidently AI)](#fase-8-observabilidad-y-monitoreo-de-deriva-evidently-ai)
   - [Fase 9: Motor de Simulación Monte Carlo y Pruebas de Estrés](#fase-9-motor-de-simulación-monte-carlo-y-pruebas-de-estrés)
   - [Fase 10: Interfaz Web Estática y Microservicio Servidor](#fase-10-interfaz-web-estática-y-microservicio-servidor)
5. [Guía Paso a Paso para Acceder e Interactuar con el Sistema](#5-guía-paso-a-paso-para-acceder-e-interactuar-con-el-sistema)
6. [Portabilidad Cruzada: Ejecución en Cualquier Máquina](#6-portabilidad-cruzada-ejecución-en-cualquier-máquina)
7. [Licencia Open Source, Derechos y Requisito Obligatorio de Atribución](#7-licencia-open-source-derechos-y-requisito-obligatorio-de-atribución)

---

## 1. Diagnóstico y Resolución del Error de Conexión (`ERR_CONNECTION_REFUSED`)

### ¿Por qué ocurrió el error en la imagen?
El navegador mostró:
```text
This site can't be reached
127.0.0.1 refused to connect.
ERR_CONNECTION_REFUSED
```

**Causa Técnica Exacta:**  
El error `ERR_CONNECTION_REFUSED` indica que en el puerto `8000` de la dirección de bucle local (`127.0.0.1` o `localhost`) no había ningún proceso de servidor escuchando conexiones TCP entrantes en ese momento. En la sesión anterior, el microservicio FastAPI se había probado internamente mediante `TestClient(app)` de Starlette/Pytest (que ejecuta las peticiones en memoria dentro del propio proceso de pruebas), pero **el servidor `uvicorn` aún no había sido iniciado como proceso daemon de fondo en el sistema operativo**.

### Solución Implementada:
El servidor ha sido puesto en marcha y se encuentra actualmente escuchando en segundo plano en:
👉 **`http://127.0.0.1:8000/`** (o **`http://localhost:8000/`**)

Para verificar o iniciar manualmente el servidor en cualquier terminal cuando lo desee, utilice:
```bash
# Método 1 (Recomendado vía Makefile):
make serve

# Método 2 (Python directo):
python -m uvicorn src.serving.api:app --host 127.0.0.1 --port 8000 --reload
```

---

## 2. Visión General y Propósito del Proyecto

El proyecto **Panamá PortOps-AI** es un ecosistema industrial completo de **Machine Learning en Producción (MLOps)** diseñado para transformar datos heterogéneos y dispersos de la Autoridad Marítima de Panamá en una infraestructura de inteligencia predictiva y resiliencia ante desastres.

### Objetivos Clave:
1. **Pronóstico Multi-Horizonte con Incertidumbre:** Estimar el volumen mensual de contenedores (TEUs) a 1–6 meses para las 6 terminales portuarias del país, entregando cuantiles probabilísticos:
   - **P10 (Escenario Pesimista):** Suelo de seguridad operacional (10% de probabilidad de caer por debajo).
   - **P50 (Pronóstico Central):** Mediana esperada para planificación financiera y de personal.
   - **P90 (Capacidad Pico):** Techo de estrés para dimensionamiento de patios y grúas pórtico (*STS*).
2. **Detección Temprana de Desbalance de Contenedores:** Alertar automáticamente sobre desbalances críticos de cajas vacías vs. llenas (`empty_ratio > 0.8`), mitigando costos de almacenamiento y requerimientos de buques de evacuación.
3. **Pruebas de Estrés Estocásticas (Monte Carlo):** Evaluar la respuesta del modelo ante eventos cisne negro (*Black Swan Events*), como restricciones de calado en el Canal de Panamá por sequías, crisis en rutas marítimas o alzas abruptas en el combustible marino (*bunkering*).
4. **100% Código Abierto y Reproducible:** Construido exclusivamente con tecnologías libres (`FastAPI`, `LightGBM`, `scipy`, `pandas`, `Streamlit`, `Chart.js`, `MLflow`, `Evidently`), sin dependencias de servicios en la nube propietarios.

---

## 3. Arquitectura Modular del Repositorio

```text
amp-cont-ai/
├── configs/
│   └── config.yaml                     # Configuración central (rutas relativas, umbrales de calidad)
├── data/
│   ├── raw/                            # Capa Bronze: 353 datasets CSV descargados de datosabiertos.gob.pa
│   ├── metadata/                       # Catálogos de datos, esquemas JSON y resultados estocásticos
│   │   ├── datasets_catalog.csv
│   │   ├── feature_distributions.json  # Parámetros de distribución y Cholesky L*L^T
│   │   └── stress_test_results.json    # Resultados multivariados y frontera de Reverse Stress Test
│   ├── silver/                         # Capa Silver: Tablas normalizadas en Apache Parquet
│   │   ├── fact_containers.parquet     # 8,986 registros atómicos deduplicados (2015-2026)
│   │   ├── fact_bunkering.parquet      # 2,267 registros de despacho de combustible marino
│   │   ├── fact_roro.parquet           # 1,256 registros de vehículos y carga rodante
│   │   └── fact_port_macro.parquet     # 770 registros de indicadores macroeconómicos
│   └── gold/                           # Capa Gold: Feature Store de Machine Learning
│       ├── container_features.parquet  # 840 filas x 85 features predictivas sin fuga
│       └── bunkering_features.parquet  # 316 filas x 81 features predictivas
├── src/
│   ├── data/
│   │   ├── classifier.py               # Motor de taxonomía y clasificación contextual
│   │   ├── normalizer.py               # Deduplicador bitemporal y transformador Silver Parquet
│   │   └── quality.py                  # Data Quality Gates con validaciones pre-ML
│   ├── features/
│   │   ├── temporal.py                 # Features cíclicas sin/cos y efecto Año Nuevo Chino
│   │   ├── maritime_ratios.py          # Ratios de trasbordo, vacíos/llenos y factor TEU/unidad
│   │   ├── lags_rolling.py             # Lags autorregresivos (t-1..t-12), rolling stats y EWMA
│   │   └── feature_store.py            # Orquestador del Feature Store Gold
│   ├── models/
│   │   ├── train.py                    # Expanding Window Backtesting con LightGBM Quantiles en MLflow
│   │   └── registry.py                 # Gobernanza y promoción Champion/Challenger en Model Registry
│   ├── simulation/
│   │   ├── __init__.py                 # Exportador público del motor de simulación
│   │   ├── distribution_profiler.py    # Ajuste MLE, bondad KS-test y Cholesky L*L^T = R
│   │   ├── monte_carlo_engine.py       # Cópula correlacionada, Merton Jump Diffusion y Block Bootstrap
│   │   └── stress_tester.py            # Evaluador de riesgo VaR (95/99%), CVaR y Reverse Stress Testing
│   ├── serving/
│   │   ├── api.py                      # Microservicio REST FastAPI con rutas /predict, /simulate y GET /
│   │   └── static/                     # Aplicación web estática desacoplada
│   │       ├── index.html              # Frontend SPA moderno en HTML5
│   │       ├── css/style.css           # Estilos marítimos responsivos, glassmorphism y dark mode
│   │       └── js/app.js               # Lógica en Vanilla JS ES6 y gráficos con Chart.js
│   ├── monitoring/
│   │   └── drift.py                    # Detección de Data Drift con Evidently AI
│   └── utils/
│       └── logger.py                   # Logging estructurado con formato profesional
├── apps/
│   └── dashboard.py                    # Dashboard analítico interactivo con Streamlit y Plotly
├── tests/
│   ├── test_quality.py                 # Pruebas de calidad y contratos de esquema
│   ├── test_features.py                # Pruebas de features cíclicas y zero-leakage
│   ├── test_model_serving.py           # Pruebas de integración del microservicio FastAPI
│   └── test_simulation.py              # Pruebas estocásticas de Cholesky, Merton y monotonía VaR/CVaR
├── reports/
│   ├── DATASET_TAXONOMY_REPORT.md      # Clasificación taxonómica de los 353 datasets
│   ├── EDA_AND_FEATURE_ENGINEERING.md  # Reporte técnico profundo de EDA y Feature Engineering
│   ├── FEATURE_BEHAVIOR_REPORT.md      # Reporte de distribuciones y correlaciones multivariadas
│   ├── MONTE_CARLO_SIMULATION_REPORT.md# Reporte ejecutivo de pruebas de estrés y Reverse Stress Test
│   └── data_drift_report.html          # Dashboard visual de deriva de datos (Evidently AI)
├── LICENSE                             # Licencia GNU GPL-3.0 con cláusula de atribución obligatoria
├── AUTHORS.md                          # Términos de reconocimiento y autoría de mbeni
├── CITATION.cff                        # Formato canónico de citación académica
├── Makefile                            # Automatización integral de tareas
└── pyproject.toml                      # Empaquetado y configuración de pytest
```

---

## 4. Explicación Detallada Fase por Fase: ¿Qué se hizo, Cómo y Por Qué?

### Fase 1: Ingesta y Clasificación Taxonómica (Capa Bronze)
- **¿Qué se hizo?** Se descargaron e indexaron 353 archivos CSV oficiales de la AMP correspondientes a los 18 períodos de páginas públicas (2015–2026), catalogándolos en [`data/metadata/datasets_catalog.csv`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/data/metadata/datasets_catalog.csv).
- **¿Cómo se hizo?** Se desarrolló [`src/data/classifier.py`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/src/data/classifier.py), que inspecciona la morfología de cada archivo, clasificándolos en 6 contextos operacionales (`CONTAINERS`, `BUNKERING`, `RORO`, `PASSENGERS`, `PILOTAGE`, `FINANCIAL`) y 2 estructuras matriciales (`LONGITUDINAL_TIME_SERIES` vs `CROSSTAB_MATRIX`).
- **¿Por qué se hizo?** Los datos gubernamentales abiertos presentan alta heterogeneidad: archivos con separadores `;` o `,`, diferentes codificaciones (`utf-8`, `latin-1`) y variantes tipográficas en encabezados (e.g. `Año`, `A\xf1o`, `Ao`). Sin una clasificación previa automatizada, no es posible aplicar normalización reproducible.

---

### Fase 2: Normalización Bitemporal (Capa Silver Parquet)
- **¿Qué se hizo?** Se generaron 4 tablas maestras normalizadas en formato columnar Apache Parquet: `fact_containers.parquet` (8,986 registros atómicos sin duplicados), `fact_bunkering.parquet`, `fact_roro.parquet` y `fact_port_macro.parquet`.
- **¿Cómo se hizo?** Mediante [`src/data/normalizer.py`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/src/data/normalizer.py). Se implementó un algoritmo de **resolución bitemporal**: los boletines de la AMP son acumulativos mensuales (e.g. el archivo de Diciembre contiene los datos de Enero a Diciembre). El normalizador indexa cada dato por `(fecha_validez, fecha_publicación)`, conservando exclusivamente el snapshot del último corte publicado, eliminando duplicados idénticos o rectificaciones intermedias.
- **¿Por qué se hizo?** Parquet reduce el tamaño en disco en más del 80%, acelera lecturas con *column-pruning* y preserva tipos de datos estrictos (`datetime64`, `float64`, `int64`), evitando lecturas repetidas de texto plano.

---

### Fase 3: Puertas de Calidad de Datos (Data Quality Gates)
- **¿Qué se hizo?** Una barrera de verificación estricta pre-ML en [`src/data/quality.py`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/src/data/quality.py).
- **¿Cómo se hizo?** Se validaron 5 dimensiones críticas:
  1. *Completitud:* Tasa de nulos $= 0.0\%$ en llaves y métricas esenciales.
  2. *Unicidad:* Cero registros duplicados para la tupla clave `(fecha, puerto, litoral)`.
  3. *Validez de Dominio:* Restricción canónica estricta a los 6 puertos oficiales y 2 litorales (`Pacífico`, `Atlántico`).
  4. *Rango Temporal:* Cobertura ininterrumpida entre 2015 y 2026.
  5. *No Negatividad Física:* Detección de ajustes contables negativos (se detectó un valor anómalo de `-111.0` TEUs rectificado a `0.0`).
- **¿Por qué se hizo?** Cumplir con el principio de *Garbage In, Garbage Out*. Un modelo entrenado con identificadores de puerto erróneos o volúmenes negativos distorsiona la convergencia de las funciones de pérdida cuantílicas.

---

### Fase 4: Ingeniería de Características y Feature Store (Capa Gold)
- **¿Qué se hizo?** Se construyó el Feature Store en [`src/features/feature_store.py`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/src/features/feature_store.py), generando `container_features.parquet` (840 filas $\times$ 85 variables) y `bunkering_features.parquet` (316 filas $\times$ 81 variables).
- **¿Cómo se hizo?** Se integraron 3 extractores modulares:
  1. **Transformaciones Cíclicas y Estacionales ([`src/features/temporal.py`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/src/features/temporal.py)):**
     $$\text{mes}_{\sin} = \sin\left(\frac{2\pi \cdot m}{12}\right), \quad \text{mes}_{\cos} = \cos\left(\frac{2\pi \cdot m}{12}\right)$$
     Preserva la continuidad matemática entre Diciembre ($m=12$) y Enero ($m=1$). Se añadieron banderas binarias de dominio para el **Año Nuevo Chino (CNY)** (impacto en Enero–Febrero) y **Temporada Alta Navideña** (Agosto–Octubre).
  2. **Ratios Operacionales Marítimos ([`src/features/maritime_ratios.py`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/src/features/maritime_ratios.py)):**
     - *Ratio de Trasbordo:* $\frac{\text{TEU trasbordo}}{\text{TEU total}}$ (captura la vocación interoceánica del puerto).
     - *Ratio de Vacíos:* $\frac{\text{TEU vacíos}}{\text{TEU llenos}}$ (medida de desbalance de equipo).
     - *Factor TEU/Unidad:* $\frac{\text{TEUs}}{\text{Cajas físicas}}$ (tamaño promedio de contenedor, modal en $\sim 1.6 - 1.8$).
  3. **Lags y Ventanas Rodantes sin Fuga Temporal ([`src/features/lags_rolling.py`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/src/features/lags_rolling.py)):**
     Lags en $t-1, t-2, t-3, t-12$ y agregaciones móviles (media, desviación estándar, mínimo, máximo y media móvil ponderada exponencialmente EWMA span 3 y 6) calculados **estrictamente sobre `.shift(1)`**, asegurando cero fuga de datos (*Zero Data Leakage*).
- **¿Por qué se hizo?** Los modelos basados en árboles requieren representaciones tabulares explícitas de la dinámica temporal y ratios normalizados para capturar patrones estacionales y tendencias sin sobreajustar.

---

### Fase 5: Análisis Exploratorio de Datos (EDA) y Hallazgos Marítimos
- **¿Qué se hizo?** Script analítico automatizado en [`analysis/eda_deep_dive.py`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/analysis/eda_deep_dive.py) que generó [`reports/EDA_AND_FEATURE_ENGINEERING.md`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/reports/EDA_AND_FEATURE_ENGINEERING.md).
- **¿Qué descubrió el análisis?**
  1. *Transición de Concentración Portuaria (Índice HHI):* El índice de Herfindahl-Hirschman pasó de un mercado altamente concentrado en 2015 ($\text{HHI} > 3,100$, duopolio Balboa–Manzanillo) a un mercado moderado y competitivo en 2024–2026 ($\text{HHI} \sim 2,200$) tras la expansión de PSA en el Pacífico.
  2. *Cuantificación del Efecto Año Nuevo Chino:* En Febrero, el índice estacional promedio cae a **0.892** (-10.8% frente a la media anual), causado por la parálisis de fábricas en Asia.
  3. *Cuantificación de Temporada Alta:* En Agosto, el índice alcanza **1.049** (+4.9%), reflejando el adelanto de inventarios retail previo a Navidad.

---

### Fase 6: Entrenamiento con Expanding Window y MLflow Tracking
- **¿Qué se hizo?** En [`src/models/train.py`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/src/models/train.py), se entrenó un ensamble de regresores por cuantiles de **LightGBM** (P10, P50, P90) con seguimiento exhaustivo en MLflow (`sqlite:///mlflow.db`).
- **¿Cómo se hizo?**
  - **Esquema de Validación:** *Expanding Window Backtesting* (entrenamiento en $[2015, t]$, validación fuera de muestra en $[t+1\text{ año}]$) en 3 cortes temporales (Split 1: 2022 post-COVID; Split 2: 2023 normalización; Split 3: 2024–2026 producción).
  - **Métrica Clave de Negocio (WAPE):**
    $$\text{WAPE} = \frac{\sum |y_i - \hat{y}_i|}{\sum y_i}$$
    Se prefiere en logística sobre el MAPE porque es inmune a la división por cero y pondera los errores por el volumen real de la terminal.
  - **Loss Function Cuantílica (Pinball Loss):**
    $$L_\alpha(y, \hat{y}) = \max(\alpha(y - \hat{y}), (1 - \alpha)(\hat{y} - y))$$
    Permite estimar directamente los percentiles $\alpha \in \{0.10, 0.50, 0.90\}$ sin asumir normalidad en los residuales.
- **Resultados:**
  - LightGBM P50 alcanzó un **WAPE entre 0.0814 y 0.0973** (error $< 9.8\%$), superando radicalmente al baseline lineal Ridge, cuyo WAPE superó el 600% por colinealidad en lags.
  - Se verificó la **monotonía de cuantiles**: $\text{P10} \le \text{P50} \le \text{P90}$.

---

### Fase 7: Gobernanza en MLflow Model Registry
- **¿Qué se hizo?** Administrador de linaje en [`src/models/registry.py`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/src/models/registry.py).
- **¿Cómo se hizo?** Valida si el último modelo entrenado cumple el umbral de producción ($\text{WAPE} \le 0.15$). Al cumplirlo, promueve automáticamente el modelo al alias productivo `@champion` bajo el nombre de registro `Panama_PortOps_LightGBM`.
- **¿Por qué se hizo?** Evita el despliegue manual o descontrolado de modelos, manteniendo una trazabilidad estricta de qué hiperparámetros, datos y métricas respaldan la versión activa en producción.

---

### Fase 8: Observabilidad y Monitoreo de Deriva (Evidently AI)
- **¿Qué se hizo?** Motor de auditoría en [`src/monitoring/drift.py`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/src/monitoring/drift.py).
- **¿Cómo se hizo?** Compara la distribución de los features en el conjunto de referencia histórico (2015–2023) contra el conjunto de producción actual (2024–2026) mediante pruebas de dos muestras de Kolmogorov-Smirnov y Wasserstein Distance.
- **Resultado:** **0.0% de deriva de datos detectada** (`status: STABLE`), documentado en el reporte interactivo [`reports/data_drift_report.html`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/reports/data_drift_report.html) y en [`data_drift_summary.json`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/reports/data_drift_summary.json).

---

### Fase 9: Motor de Simulación Monte Carlo y Pruebas de Estrés
- **¿Qué se hizo?** Tres módulos estocásticos avanzados:
  1. [`src/simulation/distribution_profiler.py`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/src/simulation/distribution_profiler.py): Ajusta distribuciones teóricas (`norm`, `lognorm`, `gamma`, `beta`, `t`) vía MLE, evalúa bondad de ajuste con Kolmogorov-Smirnov y calcula la matriz de covarianza y la factorización de Cholesky regularizada ($L_{\text{corr}} L_{\text{corr}}^T = R$).
  2. [`src/simulation/monte_carlo_engine.py`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/src/simulation/monte_carlo_engine.py): Genera trayectorias coordinadas usando:
     - **Cópula Gaussiana con Cholesky:** $\tilde{Z} = Z \cdot L^T$, preservando las correlaciones empíricas.
     - **Difusión con Saltos de Merton (1976):** Modela eventos cisne negro (sequías en el Canal, paros) con un proceso de saltos de Poisson $N_t \sim \text{Poisson}(\lambda \Delta t)$ combinado con movimiento browniano.
     - **Moving Block Bootstrap:** Remuestreo temporal en bloques contiguos ($b=3$).
  3. [`src/simulation/stress_tester.py`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/src/simulation/stress_tester.py): Evalúa las trayectorias con el modelo Champion LightGBM y cuantifica:
     - **Value at Risk (VaR 95% y 99%):** Piso mínimo de volumen con 95% o 99% de certeza estadística.
     - **Conditional Value at Risk (CVaR 95% / Expected Shortfall):** Promedio de volumen condicional en el peor 5% de los escenarios ($\mathbb{E}[Y \mid Y \le \text{VaR}_{95}]$).
     - **Reverse Stress Testing (RST):** Búsqueda en cuadrícula 2D para identificar la combinación exacta de fallas operacionales que causan una caída superior al 25%.
- **Resultado en Balboa (6 meses):**
  - *Baseline:* 198,291 TEUs esperados (VaR 95%: 176,335 TEUs).
  - *Sequía en Canal:* Contracción a 111,943 TEUs (-43.5% vs baseline; probabilidad de caída severa: 38%).
  - *Tipping Point RST:* Una caída del **60% en trasbordo** junto a un aumento del **15% en cajas vacías** rompe el umbral de solvencia de la terminal (151,924 TEUs, -25.9%).

---

### Fase 10: Interfaz Web Estática y Microservicio Servidor
- **¿Qué se hizo?**
  1. Se mejoró [`src/serving/api.py`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/src/serving/api.py) con endpoints `/predict`, `/simulate`, `/health`, `/api/ports`, `/api/history/{port}` y el montado de archivos estáticos en `GET /`.
  2. Se desarrolló el frontend estático desacoplado en [`src/serving/static/`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/src/serving/static/):
     - `index.html`: Estructura SPA con 4 pestañas interactivas.
     - `css/style.css`: Diseño marítimo responsivo profesional en modo oscuro con glassmorphism.
     - `js/app.js`: Lógica cliente en Vanilla JS ES6 y gráficos dinámicos con Chart.js.
  3. Se mantuvo el dashboard alternativo en Streamlit ([`apps/dashboard.py`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/apps/dashboard.py)).

---

## 5. Guía Paso a Paso para Acceder e Interactuar con el Sistema

### Paso 1: Iniciar el Servidor de Inferencia y Web
Abra una terminal en la raíz del proyecto y ejecute:
```bash
make serve
```
*(Alternativamente sin make: `python -m uvicorn src.serving.api:app --host 127.0.0.1 --port 8000`)*

### Paso 2: Abrir la Aplicación Web en su Navegador
Vaya a:
👉 **`http://localhost:8000/`** (o **`http://127.0.0.1:8000/`**)

### Paso 3: Interactuar con las Pestañas
1. **Pestaña "📈 Pronóstico y What-If":**
   - Seleccione una terminal (e.g. *Puerto Balboa* o *SSA Marine MIT*).
   - Ajuste el horizonte (1 a 6 meses).
   - Mueva los deslizadores de *What-If* (e.g. caída de trasbordo a -20%).
   - Haga clic en **"⚡ Generar Pronóstico en Tiempo Real"**.
   - Observe las tarjetas de KPI (P50, P10, P90, semáforo de vacíos), el gráfico de demanda con banda de incertidumbre y la tabla detallada.
2. **Pestaña "🎲 Simulación Monte Carlo y Estrés":**
   - Seleccione un escenario (e.g. *📉 Sequía Canal* o *🌪️ Cisne Negro Compuesto*).
   - Elija el número de trayectorias (100 a 500).
   - Presione **"🎲 Ejecutar Simulación Monte Carlo"**.
   - Analice las tarjetas de **VaR 95%**, **CVaR 95%**, el *Fan Chart* estocástico y el histograma de densidad de volumen final.
3. **Pestaña "🛡️ Gobernanza MLOps":**
   - Revise el estado del modelo `@champion` en MLflow y el estado de estabilidad de datos de Evidently AI.
4. **Pestaña "⚖️ Licencia Open Source y Atribución":**
   - Revise los términos de autoría y cómo citar el proyecto.

---

## 6. Portabilidad Cruzada: Ejecución en Cualquier Máquina

Todas las rutas del código fuente han sido configuradas de forma modular y relativa con `Path(__file__).resolve().parent...`. Esto garantiza que el proyecto funciona sin modificaciones en:
- **Windows (PowerShell / CMD)**
- **Linux (Ubuntu, Debian, RedHat)**
- **macOS**
- **Contenedores Docker**

### Ejecución con Docker:
```bash
# Construir la imagen Docker:
make docker-build

# Levantar con Docker Compose:
make docker-up

# Detener los servicios:
make docker-down
```

### Ejecución de Pruebas Automatizadas (22/22 Tests Pasando):
```bash
make test
```

---

## 7. Licencia Open Source, Derechos y Requisito Obligatorio de Atribución

El proyecto está formalmente protegido bajo la **GNU General Public License v3.0 (GPL-3.0)** con cláusula adicional de atribución según la Sección 7 de la licencia:

### 1. Obligación de Mantenerse Código Abierto (Copyleft Estricto)
Cualquier modificación, trabajo derivado, bifurcación (*fork*), microservicio o producto comercial que utilice este código, modelos o metodologías **debe publicarse obligatoriamente bajo la misma licencia GPL-3.0 y con su código fuente accesible de manera pública y gratuita**.

### 2. Reconocimiento y Atribución Obligatoria al Autor
En cualquier publicación, informe técnico, artículo científico, charla, repositorio público o despliegue productivo que utilice este trabajo, **se debe dar crédito explícito, claro y visible al autor original (Miguel Benítez)**:

```text
Desarrollado v1.0 Miguel Benítez
Basado en Panamá PortOps-AI por Miguel Benítez (https://github.com/miguelbenitez09/amp-cont-ai)
```

### 3. Formato Canónico de Citación Técnica (BibTeX):
```bibtex
@software{benitez2026portops,
  author       = {Benítez, Miguel},
  title        = {{Panamá PortOps-AI: Ecosistema MLOps y Motor de Simulación Estocástica para Logística Portuaria}},
  year         = {2026},
  publisher    = {GitHub},
  journal      = {GitHub repository},
  howpublished = {\url{https://github.com/miguelbenitez09/amp-cont-ai}},
  note         = {Desarrollado v1.0 Miguel Benítez. Licensed under GNU GPL v3.0 with mandatory attribution}
}
```

Para consultar los textos legales completos, diríjase a los archivos [`LICENSE`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/LICENSE), [`AUTHORS.md`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/AUTHORS.md) y [`CITATION.cff`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/CITATION.cff).
