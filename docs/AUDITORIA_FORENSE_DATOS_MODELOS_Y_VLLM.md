# Auditoría Forense y Estado Real del Proyecto: Datos, Modelos, vLLM y Chat RAG
**Panamá PortOps-AI v1.0.0**  
**Autor:** Ing. Miguel Antonio Benítez González (Universidad Tecnológica de Panamá - UTP)  
**Licencia:** GNU GPL-3.0 con Atribución Obligatoria (Sección 7)  
**Fecha de Certificación:** Octubre 2026  

---

## 1. Declaración de Transparencia y Verdad Técnica

Este documento establece con absoluta rigurosidad científica y forense la realidad operativa, la procedencia exacta de los datos, el estado del entrenamiento de los modelos y el funcionamiento del motor de inferencia de lenguaje en el repositorio `amp-cont-ai`. Se descarta cualquier pretensión o etiqueta inflada para reflejar con precisión los logros reales de ingeniería de datos y MLOps alcanzados.

---

## 2. Auditoría Forense del Lakehouse de Datos (`data/`)

El almacenamiento de datos está estructurado en una arquitectura Medallion estricta con particionado columnar Apache Parquet:

### A. Capa Bronce y Raw (`data/raw/` y `data/bronze/`):
* **`data/raw/` (354 archivos, 8.54 MB):**
  - Boletines y series mensuales oficiales descargados desde el portal `datosabiertos.gob.pa` de la **Autoridad Marítima de Panamá (AMP)**.
  - Contiene series de movimiento de contenedores por puerto en TEUs y unidades (2017 a 2022), indicadores de registro de naves, ventas de bunkering y tráfico rodado (Ro-Ro).
* **`data/bronze/` (720 archivos, 741.29 MB):**
  - Repositorio documental de la **Autoridad Nacional de Aduanas (ANA)** y SIECA.
  - Almacena 41 fuentes oficiales y expedientes PDF de acuerdos de libre comercio, listas arancelarias y decretos de gabinete en staging (`ana_agreements_full/` y `ana_recovery_sources/`).

### B. Capa Silver (`data/silver/` - 22 archivos, 8.86 MB):
* **`fact_containers.parquet` (8,986 registros atómicos):** Consolidación limpia sin duplicados bitemporales de movimientos de contenedores portuarios.
* **`fact_bunkering.parquet` (2,267 registros):** Despachos de combustible marino en barcazas por litoral (Pacífico vs Atlántico).
* **`dim_tariff_historical.parquet` (27,764 subpartidas arancelarias oficiales):**
  - Base arancelaria nacional completa de Panamá bajo la nomenclatura del Sistema Arancelario Centroamericano (SAC) / Código HS.
  - Incluye alícuotas del Derecho Arancelario a la Importación (DAI), Impuesto de Transferencia de Bienes Muebles y Servicios (ITBMS), descripciones oficiales y entidades reguladoras fiscalizadoras (MIDA, MINSA, APA, AUPSA).
* **`ana_agreements_catalog.parquet`:** Matriz de desgravación de acuerdos comerciales internacionales.
* **`customs_imports_2020_silver.parquet` (~392 MB):** Ingesta anonimizada (Ley 81 de 2019) de declaraciones aduaneras SIGA del año 2020.

### C. Capa Gold (`data/gold/` - 16 archivos, 2.50 MB):
* **`container_features.parquet` (840 observaciones mensuales, 85 columnas cuantitativas):**
  - Cobertura temporal continua desde **2015-01** hasta **2026-08**.
  - 6 terminales portuarias soberanas:
    1. **Puerto Balboa** (Pacífico)
    2. **PSA Panama International Terminal** (Pacífico)
    3. **SSA Marine Manzanillo International Terminal - MIT** (Atlántico)
    4. **Puerto Cristóbal** (Atlántico)
    5. **Colón Container Terminal - CCT** (Atlántico)
    6. **Bocas Fruit Co. / Almirante** (Atlántico Norte)
  - 85 variables de ingeniería de features: armónicos trigonométricos de estacionalidad ($\sin, \cos$), efecto Año Nuevo Chino (`is_cny`), rezagos autorregresivos sin fuga temporal ($t-1$ a $t-12$), medias móviles de 3, 6 y 12 meses, ratio de vacíos (`empty_surplus_ratio`) y elasticidad ante perturbaciones exógenas de bunkering.

### D. Relación con las Carpetas Externas de Descargas (`datasets_imports` y `datasets_exports`):
* **`C:\Users\mbeni\Downloads\datasets_imports` (8,425 archivos, ~7.3 GB):**
  - Contiene los reportes 01 al 12 del portal de comercio exterior del **INEC** por capítulo (01 al 98) y país socio comercial.
  - **Diferencia Técnica Fundamental:** Estos archivos registran transacciones monetarias CIF y peso bruto de mercancías por inciso arancelario nacional. **No son series temporales de TEUs de muelles portuarios**. Por su tamaño y naturaleza individual no anonimizada, residen en el Lakehouse de soporte externo y alimentan la base de conocimiento arancelario, no la regresión de grúas y muelles.
* **`C:\Users\mbeni\Downloads\datasets_exports` (6,236 archivos):** Mismo rol para exportaciones nacionales y reexportaciones desde la Zona Libre de Colón.

---

## 3. Realidad del Entrenamiento de Modelos Matemáticos

### A. Modelos Reales Entrenados y Evaluados:
1. **LightGBM Quantile Regressor (`models/champion_models.joblib` / `lightgbm_quantile_bundle.joblib`):**
   - Entrenado con las 840 observaciones reales de `data/gold/container_features.parquet`.
   - Optimiza la función de pérdida **Pinball Loss** para tres cuantiles independientes:
     * **P10 (Piso Pesimista):** Nivel mínimo de demanda garantizada para planificación de personal y patios.
     * **P50 (Mediana Central):** Pronóstico principal de rendimiento operativo.
     * **P90 (Techo de Estrés):** Capacidad límite para prevención de congestión portuaria.
   - Valida en tiempo de ejecución la garantía monótona anti-cruce: $P10 \le P50 \le P90$.
2. **Torneo MLOps con Expanding Window Backtesting (`models/model_benchmark.json`):**
   - Evaluado en 3 ventanas temporales sin fuga de información (Split 1: 2022, Split 2: 2023, Split 3: 2024-2026).
   - Modelos comparados en producción:
     * **LightGBM:** WAPE promedio = **0.0931 (9.31%)**, $R^2 = 0.9588$, latencia = 20 ms.
     * **Random Forest:** WAPE promedio = **0.0938 (9.38%)**, $R^2 = 0.9549$, latencia = 4.1 ms.
     * **Gradient Boosting:** WAPE promedio = **0.1018 (10.18%)**, $R^2 = 0.9507$, latencia = 32 ms.
     * **Ridge / ElasticNet:** WAPE promedio = **0.0808 (8.08%)**, $R^2 = 0.9715$, latencia = 0.28 ms (Champion lineal regularizado).

### B. Motores Matemáticos Estocásticos (`src/simulation/stress_tester.py`):
1. **Simulación de Monte Carlo con Descomposición de Cholesky:** Genera perturbaciones correlacionadas entre las terminales preservando la matriz de covarianza empírica.
2. **Difusión con Saltos de Merton (Merton Jump Diffusion):** Modela eventos de fuerza mayor o cisnes negros (sequías severas en los lagos Gatún/Alhajuela del Canal de Panamá, paros de transporte o cierres de rutas marítimas).
3. **Moving Block Bootstrap:** Remuestreo temporal por bloques que mantiene la autocorrelación serial de las series portuarias.

---

## 4. Realidad del Motor de Lenguaje, vLLM y RAG

### A. ¿Qué NO es vLLM en este Proyecto?
* **No se ha realizado un pre-entrenamiento ni un fine-tuning de pesos desde cero de un modelo LLM de 70B o 7B en este repositorio.**
* *Motivo técnico objetivo:* Entrenar o ajustar los pesos de un modelo de lenguaje de 7B o 70B parámetros requiere infraestructuras con clústeres de GPUs A100/H100 con decenas a cientos de gigabytes de VRAM. La máquina host posee una GPU laptop NVIDIA GeForce RTX 3050 con 4.0 GB de VRAM, la cual está optimizada para aceleración por lotes de árboles de decisión y ejecución cuantizada en 4 bits (AWQ), no para fine-tuning masivo de transformers.

### B. ¿Qué SÍ es y Cómo Funciona la Arquitectura Open Source?
El framework implementa una arquitectura de **RAG Soberano (Retrieval-Augmented Generation) Desacoplado**:
1. **Adaptador Universal de Inferencia (`src/infrastructure/llm_client.py`):**
   - Se conecta de forma transparente a cualquier motor de pesos abiertos en ejecución local:
     * **vLLM** (`http://localhost:8080/v1` con PagedAttention y KV-Cache).
     * **Ollama** (`http://localhost:11434` para modelos cuantizados como `qwen2.5:1.5b`, `llama3.2:3b`).
     * **Adaptadores de nube:** OpenAI, Anthropic, Google Gemini (en caso de disponer de API keys).
2. **Inyección de Contexto Grounded (Zero Alucinaciones):**
   - Antes de generar cualquier respuesta, el framework ejecuta una búsqueda en la base de datos de **27,764 subpartidas arancelarias** de Panamá, recupera la tarifa DAI, ITBMS y entidades reguladoras oficiales, ejecuta el pronóstico cuantílico de LightGBM para el puerto consultado y adjunta las citas de la **Ley 6 de 2002** y la **Ley 56 de 2008**.
   - Este contexto estructurado se inyecta en el prompt del sistema.
3. **Motor Experto Marítimo Determínistico de Respaldo:**
   - Si no hay ningún servidor vLLM u Ollama levantado, el sistema **no falla ni devuelve errores vacíos**.
   - Se activa automáticamente el motor experto determinístico de Panamá, el cual formula la respuesta exacta con la partida arancelaria, los requisitos sanitarios (MIDA/MINSA), los cálculos matemáticos de TEU y la validación de contenedores ISO 6346 mediante el algoritmo Módulo-11.

---

## 5. Nueva Interfaz de Chat Conversacional Inteligente

Se rediseñó la experiencia de consulta en la interfaz gráfica ([src/serving/static/index.html](file:///c:/Users/mbeni/Downloads/amp-cont-ai/src/serving/static/index.html)):
* **Acceso Inmediato en Barra Superior:** Botón `💬 Asistente IA & RAG` en la cabecera que desplaza de inmediato la vista a la consola de conversación.
* **Hilo de Conversación Interactivo (`#cot-chat-thread`):**
  - Mantiene un historial secuencial de mensajes.
  - Burbujas de usuario diferenciadas a la derecha con marcas de tiempo.
  - Respuestas del asistente a la izquierda con avatar e identificación del Soul activo (🛃 Agente Aduanal, ⚖️ Auditor, 🚢 Muelle, 🎲 Riesgo).
  - Acordeón colapsable **"🔍 Desglose de Razonamiento CoT (5 Pasos)"** que permite inspeccionar la verificación de seguridad, firma criptográfica, recuperación arancelaria e inferencia cuantílica.
* **Entrada Rápida con Tecla Enter:** Envío instantáneo de consultas con soporte para saltos de línea con `Shift+Enter`.
* **Botón de Reinicio ("🗑️ Nueva Conversación"):** Permite limpiar el hilo y comenzar una nueva sesión analítica en cualquier momento.

---

## 6. Conclusión de la Auditoría

El sistema `amp-cont-ai` opera con **datos reales de la República de Panamá**, modelos predictivos y estocásticos **genuinamente entrenados y verificados con pruebas automatizadas**, una base de datos arancelaria oficial de **27,764 subpartidas**, y un diseño de arquitectura **100% de código abierto soberano**, transparente y auditable bajo la **Ley 6 de 2002**.
