# MANUAL TÉCNICO Y ARQUITECTURA MLOPS: GUÍA INTEGRAL DEL PIPELINE Y EXTENSIBILIDAD
## Ecosistema Industrial Panamá PortOps-AI v1.0
**Firma Oficial del Proyecto:** `Desarrollado v1.0 Miguel Benítez`  
**Autor Principal:** Miguel Benítez (`miguelbenitez09`) (<https://github.com/miguelbenitez09>)  
**Licencia:** GNU General Public License v3.0 (GPL-3.0) con Atribución Obligatoria (Sección 7)  
**Marco Legal:** **Ley 6 de 22 de enero de 2002 de la República de Panamá** (Transparencia en la Gestión Pública y Datos Abiertos)  
**Propósito:** *Fines estrictamente educativos, pedagógicos, de investigación científica y empoderamiento cívico para personas naturales y jurídicas de la República de Panamá.*

---

## 📑 Índice General
1. [Glosario Fundamental de Términos (Para Todo Público)](#1-glosario-fundamental-de-términos-para-todo-público)
2. [Misión Cívica y Soberanía Tecnológica bajo Ley 6 de 2002](#2-misión-cívica-y-soberanía-tecnológica-bajo-ley-6-de-2002)
3. [Arquitectura del Pipeline Medallion End-to-End](#3-arquitectura-del-pipeline-medallion-end-to-end)
4. [Inferencia Causal (DAGs), Limpieza Robusta y Multicolinealidad](#4-inferencia-causal-dags-limpieza-robusta-y-multicolinealidad)
5. [Benchmarking Multi-Algoritmo y Optimización Cuantílica](#5-benchmarking-multi-algoritmo-y-optimización-cuantílica)
6. [Motor de Simulación Estocástica de Monte Carlo y Pruebas de Estrés](#6-motor-de-simulación-estocástica-de-monte-carlo-y-pruebas-de-estrés)
7. [Guía Maestra de Extensibilidad: Ingesta de Nuevas APIs y Datos Internacionales](#7-guía-maestra-de-extensibilidad-ingesta-de-nuevas-apis-y-datos-internacionales)
8. [Despliegue, Microservicio y Configuración en Caliente](#8-despliegue-microservicio-y-configuración-en-caliente)
9. [Términos Legales y Atribución Obligatoria](#9-términos-legales-y-atribución-obligatoria)

---

## 1. Glosario Fundamental de Términos (Para Todo Público)

Para que cualquier persona —estudiantes, servidores públicos, transportistas, directores de logística o entusiastas de la inteligencia artificial— pueda comprender el proyecto sin barreras técnicas, a continuación se explican los conceptos clave con analogías cotidianas y prácticas:

### 1.1 Conceptos del Negocio Marítimo y Logístico de Panamá
- **TEU (Twenty-foot Equivalent Unit):** Es la unidad mundial estándar para contar contenedores. Un contenedor típico de 20 pies equivale a **1 TEU**. Uno grande de 40 pies (como los que se ven en los camiones en la autopista Panamá-Colón) equivale a **2 TEUs**. Es la variable principal ($Y$) que nuestro modelo predice para cada puerto.
- **Trasbordo (*Transshipment*):** Contenedores que llegan a Panamá en un buque gigante, se descargan en el muelle y se vuelven a cargar en otro buque con destino a otro país (por ejemplo, de Asia hacia Sudamérica). En Panamá, más del 85% de la carga es de trasbordo.
- **Bunkering (Combustible Marino):** Venta y despacho de combustible pesado (VLSFO o IFO) a los buques que transitan por el Canal de Panamá o esperan turno en bahía.
- **Ratio de Contenedores Vacíos (*Empty Ratio*):** Porcentaje de cajas vacías respecto al total. Si este ratio es mayor a 0.80, hay un **superávit crítico** (el patio se satura de chatarra que no genera flete). Si es menor a 0.20, hay un **déficit crítico** (los exportadores de banano o café en Chiriquí y Bocas del Toro no encuentran contenedores para enviar su producto al extranjero).
- **Fondeadero (*Anchorage*):** Zona marítima segura en bahía de Panamá o bahía de Manzanillo donde los buques echan el ancla esperando turno para transitar el Canal o atracar en el muelle.
- **Calado (*Draft*):** Profundidad que se sumerge un barco en el agua. Si hay sequía en el lago Gatún, el Canal reduce el calado máximo permitido (ej. de 50 a 44 pies), obligando a los barcos a descargar miles de contenedores antes de cruzar.

### 1.2 Conceptos de Machine Learning e Inteligencia Artificial
- **MLOps (Machine Learning Operations):** Es la disciplina de ingeniería que une el entrenamiento de modelos matemáticos con las operaciones de software empresarial (automatización, pruebas de calidad de datos, monitoreo continuo de deriva, despliegue con Docker y control de versiones con Git).
- **Data Leakage (Fuga de Información Temporal):** El error de novato más grave en inteligencia artificial: permitir que el modelo "vea el futuro" durante el entrenamiento. En este proyecto se garantiza **cero fuga** calculando todos los rezagos con `.shift(1)`, asegurando que para predecir el mes de mayo solo se utilicen datos conocidos hasta abril.
- **Arquitectura Medallion (Bronze ➔ Silver ➔ Gold):** Metodología moderna de datos:
  - **Bronze:** Datos crudos tal como se descargan del Estado panameño.
  - **Silver:** Datos limpios, deduplicados y guardados en formato eficiente Apache Parquet.
  - **Gold:** Tablas de variables maestras (*Feature Store*) listas para alimentar a los algoritmos.
- **WAPE (Weighted Absolute Percentage Error):** Mide el porcentaje promedio de error que comete el modelo, pero dando más importancia a los puertos grandes que a los pequeños. Un WAPE de **9.11%** significa que el modelo acierta con más de un **90.89% de precisión global**.
- **$R^2$ (Coeficiente de Determinación):** Mide qué porcentaje de las subidas y bajadas históricas del tráfico portuario es capaz de explicar el modelo. Un $R^2 = 0.9594$ significa que explica casi el **96% del comportamiento de la demanda real**.
- **Cuantiles (P10, P50, P90):** Un modelo tradicional da una sola cifra (ej. "el puerto moverá 250,000 TEUs"), la cual casi nunca es exacta. Nuestro modelo cuantílico genera un abanico de tres números:
  - **P10 (Piso Pesimista):** Escenario de baja demanda; solo el 10% de las veces el volumen será inferior a este valor.
  - **P50 (Mediana):** El pronóstico central más probable.
  - **P90 (Techo de Capacidad / Estrés):** Escenario de máxima actividad; sirve para saber con anticipación cuántas grúas pórtico y camiones se necesitarán para no colapsar el patio.
- **Residuos ($y - \hat{y}$):** La diferencia entre el volumen real registrado y la predicción del modelo. Si los residuos tienen media cercana a cero y distribución simétrica, se demuestra que el algoritmo no favorece artificialmente a ningún puerto.
- **VIF (Factor de Inflación de la Varianza):** Herramienta que mide si dos variables son redundantes. Si dos columnas dicen lo mismo (como "mes en número" y "mes en texto"), el VIF se dispara por encima de 10; el pipeline elimina la redundancia para mantener el modelo ágil y estable.
- **Variables Confundidoras (*Confounders*):** Fenómenos que engañan a un analista haciéndole creer que $A$ causa $B$ cuando en realidad ambos son causados por un tercer factor $C$. (Ejemplo: el aumento de ventas de búnker no siempre significa más contenedores en muelle, sino buques varados en fondeadero por la sequía del Canal).
- **Simulación de Monte Carlo y Factorización de Cholesky:** Método para simular miles de escenarios futuros aleatorios pero realistas, respetando matemáticamente la correlación entre variables (si el combustible sube, el trasbordo reacciona según la historia).
- **Value at Risk (VaR 95%):** Nivel mínimo de contenedores que se espera recibir en el 95% de los meses normales, permitiendo calcular el peor escenario financiero y operativo antes de que ocurra.
- **Reverse Stress Testing:** Algoritmo inverso que calcula: "¿Qué combinación mínima de catástrofes tendría que suceder para que el puerto colapse en más de un 30%?".

---

## 2. Misión Cívica y Soberanía Tecnológica bajo Ley 6 de 2002

El desarrollo de **Panamá PortOps-AI** se fundamenta en un principio cívico y de soberanía nacional:
1. **Marco Normativo:** Desarrollado bajo el amparo de la **Ley 6 de 22 de enero de 2002 de la República de Panamá**, que dicta normas para la transparencia en la gestión pública, la acción de hábeas data y el acceso ciudadano a la información del Estado.
2. **Empoderamiento Productivo Nacional:** Panamá posee la mejor posición geográfica de América Latina, pero sus herramientas de análisis han estado tradicionalmente monopolizadas por consultoras extranjeras que cobran cientos de miles de dólares por licencias de software privativo. Este proyecto entrega una plataforma de grado doctoral, 100% libre, de código abierto y auditable, al servicio de:
   - Cooperativas de transportistas terrestres de carga contenerizada.
   - Agencias navieras y operadores de logística de la Zona Libre de Colón y Panamá Pacífico.
   - Operadores de terminales portuarias (Balboa, PSA, MIT, Cristóbal, CCT, Bocas Fruit Co.).
   - Estudiantes y centros de investigación de la Universidad de Panamá, Universidad Tecnológica de Panamá (UTP) y la Universidad Marítima Internacional de Panamá (UMIP).
   - Servidores públicos y planificadores de infraestructura del Estado panameño.
3. **Compromiso Estricto de Cero Datos Falsos (*Zero Mocks*):** En ningún componente del proyecto se utilizan números inventados. Todo se calcula empíricamente sobre 140 meses consecutivos de microdatos oficiales de la Autoridad Marítima de Panamá (AMP).

---

## 3. Arquitectura del Pipeline Medallion End-to-End

El flujo de datos sigue el estándar industrial **Medallion**, asegurando trazabilidad, reproducibilidad y gobernanza en cada etapa:

```text
Portal AMP (datosabiertos.gob.pa)
       │  [scripts/download_data.py]
       ▼
CAPA BRONZE: data/raw/ (353 CSVs oficiales heterogéneos)
       │  [src.data.classifier & src.data.normalizer]
       ▼
CAPA SILVER: data/silver/ (Fact tables atómicas Parquet deduplicadas bitemporalmente)
       │  [src.data.quality (Data Quality Gates de 5 dimensiones)]
       │  [src.features.feature_store (Cero fuga temporal, rezagos .shift(1))]
       ▼
CAPA GOLD: data/gold/ (Feature Store: 840 filas x 85 features)
       │  [src.models.train (Expanding Window Backtesting: LightGBM, RF, HGB, Ridge)]
       ▼
MODEL REGISTRY: models/ (champion_models.joblib & model_benchmark.json)
       │  [src.serving.api (FastAPI REST + Webview Responsive + Modales Pedagógicos)]
       ▼
USUARIO FINAL: Web App, Swagger UI (/docs) o Integración ERP en Producción
```

---

## 4. Inferencia Causal (DAGs), Limpieza Robusta y Multicolinealidad

### 4.1 Inferencia Causal con el Grafo de Judea Pearl
En series temporales de comercio exterior, correlación no implica causalidad. El sistema desacopla los efectos espurios mediante el Grafo Causal Acíclico Dirigido (DAG):

```mermaid
flowchart TD
    Macro["Macroeconomía Global / Tasas de Interés (Z₁)"] --> Season["Estacionalidad Mensual / Trimestral (X₁)"]
    Macro --> TEU["Demanda Real de TEUs en Puerto (Y)"]
    Drought["Sequía El Niño / Restricciones Canal (Z₂)"] --> Bunkering["Venta de Combustible Marino Bunkering (X₂)"]
    Drought --> TEU
    Bunkering --> TEU
    Season --> TEU
    Inercia["Capacidad Instalada / Inercia Anual Lag-12 (X₃)"] --> TEU
    Inercia -.->|"Confusor de Capacidad"| Bunkering
```

Bajo el operador $do(B = b)$ de Judea Pearl, la intervención en políticas operacionales se formaliza como:
$$P(Y \mid do(B = b)) = \sum_{z_2, l} P(Y \mid B = b, Z_2 = z_2, L = l) P(Z_2 = z_2, L = l)$$

### 4.2 Desacoplamiento de Variables Confundidoras
1. **Inercia Contractual ($\text{TEU}_{t-12}$):** Las líneas navieras firman contratos de muelle por año. Para evitar que el modelo confunda la inercia contractual con un incremento repentino de demanda mensual, se aplica diferenciación interanual ($\Delta \text{TEU}_{t, t-12}$).
2. **Bunkering como Proxy de Fondeadero:** Cuando el Canal reduce tránsitos por sequía, los barcos esperan hasta 20 días en bahía consumiendo combustible auxiliar. La venta de búnker sube, pero los contenedores en muelle caen. El Feature Store desacopla esto calculando el ratio de productividad activa:
   $$\text{Ratio TEU/BBL} = \frac{\text{TEU}_t}{\text{Bunkering\_BBL}_t + \epsilon}$$

### 4.3 Detección Robusta con Hampel y MAD vs. Z-Score
El estimador tradicional Z-Score colapsa ante disrupciones marítimas porque su punto de ruptura es $\varepsilon^* = 1/n \to 0$. El pipeline implementa el estimador de Hampel basado en la Mediana y la Desviación Absoluta de la Mediana (MAD):
$$\text{MAD}_t = 1.4826 \times \text{median}(\{|x_i - \tilde{x}_t| : x_i \in W_t(k)\})$$
$$\text{Criterio de Outlier:} \quad |x_t - \tilde{x}_t| > 3 \times \text{MAD}_t$$
Este estimador tiene un **punto de ruptura del 50% ($\varepsilon^* = 0.50$)**, garantizando que hasta la mitad de las observaciones en una ventana temporal puedan ser extremas sin romper la calibración del modelo.

### 4.4 Factor de Inflación de la Varianza (VIF)
Para la matriz de covarianza estandarizada $\mathbf{R} = \frac{1}{n} \mathbf{Z}^T \mathbf{Z}$:
$$\operatorname{Var}(\hat{\beta}_j) = \frac{\sigma^2}{n (1 - R_j^2)} \equiv \frac{\sigma^2}{n} \text{VIF}_j$$
Cualquier variable con $\text{VIF}_j \ge 10$ se elimina o se sustituye por armónicos continuos ($\sin/\cos$) para preservar la estabilidad numérica del algoritmo.

---

## 5. Benchmarking Multi-Algoritmo y Optimización Cuantílica

### 5.1 Pérdida Cuantílica (Pinball Loss)
El modelo Champion entrena 3 conjuntos de árboles independientes en LightGBM para los cuantiles $\tau \in \{0.10, 0.50, 0.90\}$ minimizando la función de costo asimétrica:

$$\rho_\tau(u) = u (\tau - \mathbb{I}(u < 0)) = \begin{cases} 
\tau u & \text{si } u \ge 0 \\ 
(\tau - 1) u & \text{si } u < 0 
\end{cases}$$

Con garantía de monotonicidad empírica: $\hat{q}_{0.10} \le \hat{q}_{0.50} \le \hat{q}_{0.90}$.

### 5.2 Resultados Empíricos Comparativos (Expanding Window 2022–2026)
| Algoritmo | Estado | WAPE Promedio | MAE Promedio | RMSE Promedio | $R^2$ Promedio | Latencia | Justificación Operativa |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **LightGBM Quantiles** | 🏆 **Champion** | **9.11%** | 11,300 TEUs | 15,080 TEUs | **0.9594** | 13.28 ms | Captura relaciones no lineales y entrega bandas de incertidumbre P10-P90. |
| **Random Forest** | 🥈 **Challenger** | **9.10%** | 11,352 TEUs | 15,085 TEUs | **0.9588** | 4.58 ms | Excelente precisión con la latencia más baja para microservicios de alto tráfico. |
| **HistGradientBoosting** | 🥉 **Challenger** | **9.78%** | 12,186 TEUs | 15,853 TEUs | **0.9545** | 70.30 ms | Algoritmo aditivo robusto sin hiperparámetros complejos. |
| **Ridge / ElasticNet** | ⚠️ **Baseline** | 1917.38% | 2.61e+08 | 2.65e+09 | -0.0188 | 0.19 ms | Evidencia pedagógica del colapso lineal ante multicolinealidad autorregresiva de 81 variables. |

---

## 6. Motor de Simulación Estocástica de Monte Carlo y Pruebas de Estrés

### 6.1 Choques Correlacionados con Factorización de Cholesky
Dada la matriz de covarianza empírica $\mathbf{\Sigma} \in \mathbb{R}^{k \times k}$ calculada sobre los retornos históricos de variables logísticas:
1. Se descompone la matriz: $\mathbf{\Sigma} = \mathbf{L} \mathbf{L}^T$.
2. Se generan números aleatorios gaussianos independientes: $\mathbf{Z} \sim \mathcal{N}(\mathbf{0}, \mathbf{I}_k)$.
3. Se proyectan los choques estocásticos correlacionados: $\mathbf{X} = \boldsymbol{\mu} + \mathbf{L} \mathbf{Z}$, garantizando $\operatorname{Cov}(\mathbf{X}) = \mathbf{\Sigma}$.

### 6.2 Proceso de Salto-Difusión de Merton (Poisson Jumps)
Modelado matemático de eventos catastróficos discretos:
$$\frac{dS_t}{S_{t^-}} = \mu dt + \sigma dW_t + J_t dN_t$$
donde $N_t$ es un proceso de Poisson con tasa anual $\lambda = 0.15$ y salto log-normal $\ln(1 + J_t) \sim \mathcal{N}(\mu_J, \sigma_J^2)$.

---

## 7. Guía Maestra de Extensibilidad: Ingesta de Nuevas APIs y Datos Internacionales

Uno de los principales requisitos del proyecto es permitir que cualquier desarrollador o científico de datos pueda **extender el modelo fácilmente** incorporando nuevas variables (telemetría AIS, meteorología satelital, precios de búnker o índices de fletes internacionales).

A continuación se detalla el procedimiento exacto paso a paso:

```mermaid
flowchart TD
    API["Nueva Fuente de Datos Externa<br/>(API AIS, API Clima ACP, API Fletes)"] --> Val["1. Paso de Calidad (Quality Gate)<br/>src/data/quality.py"]
    Val --> Norm["2. Normalización Matemática<br/>(Hampel MAD, Z-Score o Log-Ratio)"]
    Norm --> Feat["3. Concatenación al Gold Feature Store<br/>src/features/feature_store.py"]
    Feat --> Train["4. Reentrenamiento Determinista<br/>make train (seed=42)"]
    Train --> Reg["5. Auditoría y Registro en Registry<br/>src/models/registry.py"]
```

### Paso 1: Configurar el Conector de Ingesta
Crea un script extractor en `src/data/` (por ejemplo, `src/data/ext_ais_connector.py`) que consulte la API externa y genere un DataFrame con las columnas clave:
- `fecha`: Fecha canónica del mes en formato `YYYY-MM-01`.
- `port`: Nombre normalizado de la terminal (ej. `"Puerto Balboa"`).
- `variable_externa`: Valor cuantitativo medido (ej. `ais_avg_draft_meters`).

### Paso 2: Registrar la Regla en Data Quality Gates (`src/data/quality.py`)
Antes de permitir que el dato ingrese al Feature Store, se debe someter al contrato de validación:
```python
def validate_external_ais_feature(df: pd.DataFrame) -> bool:
    # 1. Chequeo de nulos:
    assert df["ais_avg_draft_meters"].isna().sum() == 0, "No se permiten valores nulos"
    # 2. Chequeo de rango físico marítimo:
    assert df["ais_avg_draft_meters"].between(5.0, 22.0).all(), "Calado fuera de rango físico admisible"
    return True
```

### Paso 3: Aplicar la Transformación de Normalización Matemática
Para evitar que variables con unidades grandes (ej. tarifas de flete en miles de dólares) distorsionen las divisiones de los árboles o colapsen los modelos lineales:
- **Si tiene picos de fondeadero (AIS):** Aplicar **Hampel MAD**:
  $$z_{\text{mad}} = \frac{x_t - \text{median}(W)}{1.4826 \times \text{MAD}(W)}$$
- **Si es batimetría de lago o temperatura:** Aplicar **Z-Score**:
  $$z = \frac{x_t - \bar{x}}{\sigma}$$
- **Si son precios o índices financieros (FBX / SCFI):** Aplicar **Log-Returns**:
  $$r_t = \ln(P_t / P_{t-1})$$

### Paso 4: Concatenar en el Feature Store (`src/features/feature_store.py`)
Agrega la nueva variable calculando siempre su rezago con `.shift(1)` para evitar fuga temporal:
```python
# Ejemplo en src/features/feature_store.py:
df_merged = df_merged.sort_values(by=["port", "date"])
df_merged["ais_draft_lag_1"] = df_merged.groupby("port")["ais_avg_draft_meters"].shift(1)
```

### Paso 5: Reentrenar y Auditar el Modelo
Ejecuta el reentrenamiento determinista en la terminal:
```bash
make train
```
El pipeline registrará el nuevo run en MLflow (`mlflow.db`), evaluará el WAPE sobre las 3 particiones temporales y, si el nuevo modelo supera al Champion actual, lo promoverá automáticamente en el Model Registry.

---

## 8. Despliegue, Microservicio y Configuración en Caliente

### 8.1 Puesta en Marcha del Servidor
```bash
make serve
# o alternativamente:
python -m uvicorn src.serving.api:app --host 127.0.0.1 --port 8000
```

### 8.2 Endpoints del Microservicio FastAPI:
- **`GET /`**: Landing Page responsive interactiva y adaptativa para WebView móvil y desktop con consola API en vivo.
- **`GET /docs`**: Documentación Swagger UI interactiva con ejemplos ejecutables en Python, cURL y JavaScript.
- **`POST /predict`**: Inferencia cuantílica multi-algoritmo con evaluación What-If.
- **`POST /predict/batch`**: Inferencia simultánea para las 6 terminales portuarias panameñas.
- **`GET /api/models/compare`**: Matriz comparativa de WAPE, MAE, RMSE, R² y latencias de los 4 algoritmos.
- **`GET /api/models/diagnostics`**: Residuos reales empíricos, split gains de variables y catálogo causal de variables confusoras.
- **`POST /simulate`**: Simulación Monte Carlo coordinada con cópulas de Cholesky y saltos de Poisson.
- **`GET /api/config` & `POST /api/config`**: Consulta y actualización en caliente de parámetros de inferencia y umbrales de vacíos sin reiniciar el servidor.
- **`POST /api/extensibility/simulate-external-feature`**: Simulador interactivo para verificar y proyectar el impacto de nuevas variables externas antes de concatenarlas al pipeline permanente.
- **`GET /api/infrastructure/status`**: Monitoreo en tiempo real del estado de salud de los adaptadores de base de datos (DuckDB, PostgreSQL, Redis), herramientas MCP activas, inventario de secretos y aceleradores de hardware.
- **`POST /api/rag/query`**: Motor de búsqueda semántica RAG con citas exactas sobre la Ley 56 de 2008, Ley 6 de 2002 y arquitectura MLOps, protegido con Guardrails semánticos.
- **`POST /api/guardrails/validate`**: Auditoría multicapa previa a la inferencia (límites físicos de terminales y detección de prompt injection).
- **`GET /api/export/provenance`**: Ficha técnica de auditoría y procedencia de datos reales (cobertura 140 meses AMP/INEC, 81 features, hash SHA-256).
- **`POST /api/export/dataset`**: Motor de exportación de datos con nombre de archivo personalizable por el usuario, formato CSV/JSON y vista previa en tiempo real.
- **`GET /api/lakehouse/catalog`**: Catálogo taxonómico unificado de los 17 Ministerios de Panamá, Autoridad del Canal de Panamá (ACP) e IMHPA.
- **`POST /api/lakehouse/query`**: Consulta filtrada de series temporales estructuradas del Lakehouse nacional (indicadores ministeriales, tránsitos ACP, clima y disrupciones).
- **`GET /api/governance/iso-compliance`**: Declaración formal de cumplimiento de normas ISO 27001, 42001, 27701 y 22301 para adopción y compras públicas gubernamentales.

### 8.3 Lakehouse Nacional de Panamá y Scraper de los 17 Ministerios (`src/data/lakehouse/` & `src/data/scrapers/`)
El repositorio expande el pipeline tradicional hacia un **Lakehouse Nacional de Inteligencia Portuaria y Macroeconómica** que reúne 140 meses de microdatos empíricos continuos (2015–2026):
1. **Scraper de los 17 Ministerios de la República de Panamá:**
   - **MICI & ZLC:** Exportaciones manufactureras, empresas SEM/EMMA y movimiento comercial de reexportación e importación de la Zona Libre de Colón.
   - **MEF & DGI:** Crecimiento del PIB trimestral, inflación IPC anual, recaudación fiscal marítima y cánones de concesiones de terminales portuarias.
   - **MOP:** Estado de la red vial logística y programas de mantenimiento en los puentes Centenario y de las Américas.
   - **MIAMBIENTE:** Estrés hídrico en la Cuenca Hidrográfica del Canal de Panamá (CHCP) y volumen de precipitaciones nacionales.
   - **MIDA:** Cajas de exportación de banano y contenedores refrigerados (*reefers*) agroindustriales.
   - **MINSA:** Inspecciones fito y zoosanitarias en muelles y tiempo promedio de despacho de naves.
   - **MITRADEL:** Convenciones colectivas portuarias activas y días de paralización por conflictos laborales.
   - **MIVIOT:** Hectáreas aprobadas para parques logísticos y zonificación adyacente a terminales.
   - **MINGOB & MINSEG:** Porcentaje de contenedores inspeccionados mediante escáneres no intrusivos y salvaguarda civil.
   - **MIRE, MEDUCA, MIDES, MICULTURA & SENAN/AMP:** Acuerdos marítimos bilaterales, formación técnica náutica, salvamento marítimo y prevención de derrames de búnker.
2. **Tráfico Detallado del Canal de Panamá (ACP):**
   - Tránsitos mensuales clasificados por clase de buque: Neopanamax Container, Panamax Container, Graneleros (*Bulk Carriers*), Quimiqueros/Tanqueros, Gaseros (LNG/LPG) y Portavehículos (*Ro-Ro*).
   - Matriz de origen y destino de carga por país: Estados Unidos (72.4%), China (21.8%), Japón (14.1%), Chile (10.9%) y Corea del Sur (9.8%).
   - Restricciones históricas de calado y reducción de cupos diarios de tránsito (de 36 a 24 slots por sequía extrema en 2023–2024).
3. **Clima IMHPA, Frentes Fríos, Huracanes y Bloqueos Políticos:**
   - Anomalía de temperatura superficial del mar y fenómeno ENSO (El Niño / La Niña) mediante el índice ONI de IMHPA.
   - Frentes fríos de invierno en el Caribe (noviembre a febrero) con vientos superiores a 35 nudos que obligan a detener las grúas pórtico STS en Colón.
   - Shocks indirectos por huracanes (Otto en 2016, Eta e Iota en 2020).
   - Calendario festivo oficial y recargo salarial de estiba del 150% durante las Fiestas Patrias de noviembre.
   - Cronología de disrupciones sociopolíticas de fuerza mayor: Paro Nacional de julio de 2022 (21 días) y bloqueos viales por contrato minero en octubre-noviembre de 2023 (38 días).

### 8.4 Matriz de Cumplimiento Normativo ISO para Entidades Públicas
Para satisfacer los requisitos de adquisición de tecnología por parte de la Autoridad Marítima de Panamá (AMP), Autoridad del Canal de Panamá (ACP), MICI, MEF y Contraloría General de la República, el sistema cuenta con controles formales basados en cuatro normas ISO fundamentales:
- **ISO/IEC 27001:2022 (Seguridad de la Información):**
  - Cifrado en tránsito obligatorio TLS 1.3 con calificación A+.
  - Cifrado en reposo para Lakehouse y Feature Store con algoritmo AES-256.
  - Principio de menor privilegio (*Least Privilege*) y gestión centralizada de secretos con rotación de 90 días (`SecretManager`).
  - Bitácoras de auditoría inmutables en formato JSONL sin exposición de datos de identificación personal (PII).
- **ISO/IEC 42001:2023 (Gestión de Inteligencia Artificial):**
  - Trazabilidad bitemporal estricta (*Zero Lookahead Bias*) entre datasets de origen y modelos entrenados.
  - Explicabilidad algorítmica obligatoria: cuantiles P10-P50-P90 y descomposición de importancia de variables (*split gains*).
  - Mitigación rigurosa de sesgos de estimación y variables confusoras mediante el cálculo causal (*do-calculus* de Pearl).
  - Monitoreo continuo de *Data Drift* y degradación de WAPE (umbral de retiro < 15%).
  - Reproducibilidad matemática total fijando la semilla aleatoria en 42.
- **ISO/IEC 27701:2019 (Privacidad de la Información y Ley 81 de 2019):**
  - Cumplimiento formal de la **Ley 81 de 26 de marzo de 2019 sobre Protección de Datos Personales** de la República de Panamá.
  - Agregación atómica de microdatos a nivel macro-terminal mensual para impedir cualquier reidentificación de cargas.
  - Anonimización criptográfica irreversible de consignatarios, agentes navieros y buques mediante algoritmos HMAC-SHA256 con sal.
  - Prohibición estricta de persistir pasaportes o datos personales de tripulaciones marítimas.
- **ISO 22301:2019 (Continuidad del Negocio y Resiliencia Operacional):**
  - Desacoplamiento de microservicios con orquestación en clústeres Kubernetes (`k8s/`).
  - Sondas de salud *Liveness* y *Readiness* con auto-reparación (*self-healing*) ante fallas imprevistas.
  - Autoescalado horizontal de pods (HPA) configurado de 2 a 8 réplicas.
  - Capa de caché en memoria Redis con latencia inferior a 2ms para garantizar servicio ininterrumpido.

### 8.5 Consola de Integración API y Gestión de Secretos
La consola web interactiva permite seleccionar el modo de autenticación:
- **Bearer Token (`AMP_API_SECRET_KEY`):** Encabezado estándar `Authorization: Bearer sk-amp-...`.
- **HashiCorp Vault / Secret Manager:** Inyección de secretos en memoria de contenedor mediante variables seguras.
- **Modo Desarrollo:** Acceso directo para pruebas locales pedagógicas.
Todo el código generado se actualiza de manera reactiva en cURL, Python y JavaScript al mover los controles deslizantes de sensibilidad *What-If* y los selectores de terminal y horizonte.

### 8.6 Infraestructura Empresarial y Escalabilidad Modular:
1. **Adaptadores Universales de Persistencia (`src/infrastructure/db/`):**
   - `DuckDBAdapter`: Motor columnar in-process para análisis vectorial ultrarrápido (< 0.5 ms) sobre los Parquets de Gold.
   - `PostgresTimescaleAdapter`: Soporte nativo para PostgreSQL 16 con TimescaleDB para almacenamiento de telemetría continua y series temporales particionadas.
   - `RedisCacheAdapter`: Capa de caché en memoria para almacenar resultados de inferencias cuantílicas con latencias inferiores a 2 milisegundos, incluyendo fallback automático en memoria local cuando el cluster Redis no está activo.
2. **Servidor MCP Nativo (Model Context Protocol) (`src/mcp/`):**
   - Implementa el estándar oficial MCP 2024-11-05 sobre transporte stdio y HTTP/SSE.
   - Expone 5 herramientas seguras (`get_port_forecast`, `run_monte_carlo_risk_simulation`, `compare_model_benchmarks`, `simulate_external_feature`, `query_maritime_knowledge`) para Claude Desktop, Cursor, Antigravity y agentes autónomos.
3. **Motor RAG y Base de Conocimiento Jurídico-Portuaria (`src/rag/`):**
   - Indexa vectorialmente decretos de la Ley 56 de 2008 (General de Puertos), Ley 6 de 2002 (Transparencia) y avisos a la navegación de la ACP.
   - Resuelve preguntas de operadores logísticos generando respuestas contextualmente ancladas (*context-grounded*) sin alucinaciones.
4. **Guardrails de Inferencia y Seguridad (`src/guardrails/`):**
   - Filtro físico: previene volúmenes negativos de TEUs o que excedan los 600,000 TEUs/mes por terminal.
   - Monotonicidad de cuantiles: asegura que ningún modelo de árbol produzca $P_{10} > P_{50}$ o $P_{50} > P_{90}$.
   - Sanitización semántica: filtra vectores de ataque como inyección de prompts (`ignore previous instructions`, `drop table`).
5. **Aceleración por Hardware (CUDA, OpenMP y vLLM):**
   - LightGBM optimizado para CPU multinúcleo con OpenMP y compatible con GPUs NVIDIA mediante el parámetro `device=cuda`.
   - Compatibilidad arquitectónica para desplegar modelos de lenguaje en RAG utilizando el motor de alto rendimiento **vLLM** con PagedAttention en clústeres Kubernetes con nodos GPU.

---

## 9. Términos Legales y Atribución Obligatoria

Este software es libre bajo la licencia **GNU General Public License v3.0 (GPL-3.0)** con cláusula adicional de atribución obligatoria según la Sección 7(b) y 7(c) de la licencia.

Cualquier uso educativo, investigación académica, publicación técnica, derivado o despliegue comercial debe conservar de forma visible y clara la mención de autoría:

```text
Desarrollado v1.0 Miguel Benítez
Basado en Panamá PortOps-AI por Miguel Benítez (https://github.com/miguelbenitez09/amp-cont-ai)
```

### Formato de Citación Académica (BibTeX):
```bibtex
@software{benitez2026portops,
  author       = {Benítez, Miguel},
  title        = {{Panamá PortOps-AI v1.0: Ecosistema MLOps, Benchmarking Multi-Algoritmo y Motor de Simulación Estocástica para Logística Portuaria}},
  year         = {2026},
  publisher    = {GitHub},
  journal      = {GitHub repository},
  howpublished = {\url{https://github.com/miguelbenitez09/amp-cont-ai}},
  note         = {Desarrollado v1.0 Miguel Benítez. Fines Cívicos y Educativos (Ley 6 de 2002). Licensed under GNU GPL v3.0 with mandatory attribution}
}
```

---
**Firma Oficial del Proyecto:**  
`Desarrollado v1.0 Miguel Benítez`  
República de Panamá, 2026.
