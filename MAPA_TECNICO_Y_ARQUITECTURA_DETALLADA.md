# MAPA INTEGRAL DEL SISTEMA, ARQUITECTURA Y AUDITORÍA DE CÓDIGO FUENTE
## AMP-CONT-AI (Panamá PortOps-AI v2.0.0-candidate)
**Autor y Titular:** Ing. Miguel Antonio Benítez González (Universidad Tecnológica de Panamá - UTP)  
**Licencia:** GNU General Public License v3.0 (GPL-3.0) con Atribución Obligatoria (Sección 7)  
**Estado del Ciclo de Vida:** `PRODUCTION_CANDIDATE` (Bajo Metodología LOOP Engineering)  
**Fecha de Auditoría:** Octubre 2026  

---

## 1. RESUMEN EJECUTIVO Y VERDAD ABSOLUTA DEL SISTEMA

Este documento constituye la **auditoría técnica exhaustiva y mapa formal de ingeniería inversa** del repositorio `amp-cont-ai`. Representa con fidelidad matemática y operativa el estado real del software:
- **Zero Mocks:** No se declaran capacidades simuladas ni pesos inexistentes.
- **Doble Entrada de Red (Dual-Port Gateway Architecture):**
  - **Puerto 8000 (`cmd/gateway/main.go`):** Gateway de alto rendimiento compilado en Go con inyección de cabeceras de seguridad HSTS/CSP, caché estática en memoria con ETag, rate limiting por token bucket y proxy inverso hacia el backend.
  - **Puerto 8001 (`src/serving/api.py`):** Worker ASGI FastAPI / Uvicorn con 73 rutas registradas, 12 roles RBAC, 31 permisos, catálogo de 27,764 aranceles de Panamá (ANA), Lakehouse Medallion y registro de modelos.
- **Fuente Autoritaria de Verdad:** Todo agente o usuario debe consultar [`project_brain/`](file:///c:/Users/mbeni/Downloads/amp-cont-ai/project_brain/) para conocer el estado vivo de brechas, capacidades, modelos y políticas criptográficas.

---

## 2. MAPA ESTRUCTURAL DE DIRECTORIOS Y ARCHIVOS

```
amp-cont-ai/
├── cmd/
│   └── gateway/
│       └── main.go                         # Gateway HTTP en Go (Puerto 8000), Proxy Inverso, WAF y Caché
├── project_brain/
│   ├── SYSTEM_SOURCE_OF_TRUTH.yaml         # Fuente única de verdad del estado del runtime
│   ├── CAPABILITY_MATRIX.yaml              # Matriz de 12 roles y capacidades granulares
│   ├── GAP_REGISTER.yaml                   # Registro formal de brechas UI/ARCH/BRAIN
│   ├── MODEL_CATALOG.yaml                  # Catálogo formal de modelos y métricas
│   ├── DATA_CATALOG.yaml                   # Esquemas Medallion (Bronze/Silver/Gold)
│   └── SECURITY_BASELINE.yaml              # Políticas criptográficas y de red
├── src/
│   ├── agents/                             # Enjambre agéntico marítimo y aduanero
│   ├── auth/                               # Motor IAM, JWT, RBAC, WORM Ledger y Password Policy
│   ├── brain/                              # Servicio API para consultar el Project Brain
│   ├── data/                               # Pipelines Medallion, Scrapers y Parsers ISO 6346
│   ├── features/                           # Feature Store de 85 variables sin lookahead bias
│   ├── framework/                          # Configuración, runtime y app de la plataforma
│   ├── governance/                         # Colas de brechas y gobernanza LOOP
│   ├── guardrails/                         # Guardrails semánticos, físicos y cuantílicos
│   ├── infrastructure/                     # Adaptadores DB (DuckDB/PostgreSQL/Redis), Hardware y Wazuh
│   ├── mcp/                                # Servidor Model Context Protocol (JSON-RPC 2.0)
│   ├── models/                             # Modelos LightGBM Cuantílicos, Torneo y Registry
│   ├── monitoring/                         # Drift conceptual y de datos (Evidently/KS-Test)
│   ├── platform/                           # Gestión de plugins, runtimes (vLLM/Ollama) y políticas
│   ├── rag/                                # Motor RAG Soberano sobre leyes y aranceles
│   ├── serving/                            # API FastAPI, V1 Router y Assets de Frontend
│   ├── simulation/                         # Motor Monte Carlo, Cópalas de Cholesky y Saltos Merton
│   └── utils/                              # Utilidades de logging estructurado
├── scripts/                                # Scripts de bootstrap, entrenamiento y auditoría
├── tests/                                  # Suite de 90 tests automatizados (Pytest)
└── Dockerfile, docker-compose.yml          # Manifiestos de contenerización estandarizados
```

---

## 3. AUDITORÍA DETALLADA MÓDULO POR MÓDULO

### 3.1 Entrada de Red y Perímetro: Go Gateway (`cmd/gateway/main.go`)
- **Propósito:** Actuar como escudo perimetral público en el puerto `8000`.
- **Estructuras Clave:**
  - `RateLimiter`: Implementa el algoritmo Token Bucket por dirección IP (tasa: 120 req/min, ráfaga: 30) con recolección de basura de IPs inactivas cada 5 minutos.
  - `Metrics`: Contabiliza de manera atómica (`atomic.AddUint64`) peticiones totales, proxy, estáticas y fallidas.
  - `ReverseProxy`: Enruta el tráfico hacia `http://127.0.0.1:8001` agregando cabeceras `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Gateway-Engine: Go-NetHTTP` y generando un identificador criptográfico único `X-Request-ID` (`req_<hex>`).
- **Políticas de Cabeceras HTTP Inyectadas:**
  - `Content-Security-Policy`: Restringe scripts y estilos a fuentes locales y CDNs aprobados (KaTeX, Chart.js).
  - `Strict-Transport-Security`: HSTS con directiva `max-age=31536000; includeSubDomains`.
  - `X-Content-Type-Options: nosniff` y `X-Frame-Options: SAMEORIGIN`.
- **Enrutamiento Determinista:**
  - `GET /` $\rightarrow$ Entrega `landing.html` (Landing page corporativa con SSR y diseño limpio).
  - `GET /app` $\rightarrow$ Entrega `index.html` (Estación de mando y dashboard analítico).
  - `GET /health/gateway` $\rightarrow$ Endpoint de healthcheck (`{"status":"healthy","engine":"go_gateway"}`).
  - `GET /metrics` $\rightarrow$ Métricas de tráfico en formato compatible Prometheus.
  - `/api/*`, `/docs`, `/openapi.json`, `/predict` $\rightarrow$ Redirigidos transparentemente a FastAPI (8001).

---

### 3.2 Núcleo Operacional y Servidor de Inferencia: FastAPI (`src/serving/api.py` y `v1_router.py`)
- **Propósito:** Microservicio analítico y transaccional en el puerto `8001`.
- **Rutas Principales Registradas:**
  - `POST /predict`: Inferencia cuantílica sobre terminales de Panamá (`Puerto Balboa`, `SSA Marine MIT`, `Puerto Cristóbal`, etc.). Retorna bandas $P_{10}$ (piso), $P_{50}$ (mediana) y $P_{90}$ (techo) garantizando no-cruce isotónico ($P_{10} \le P_{50} \le P_{90}$).
  - `POST /simulate`: Ejecución del motor estocástico de Monte Carlo con choques de Cholesky y procesos de Merton.
  - `GET /api/v1/auth/first-run/status`: Inspección del estado del asistente de primer inicio.
  - `POST /api/v1/auth/first-run/change-root-password`: Cambio forzado de la contraseña de superadministrador `root` con cumplimiento NIST SP 800-63B.
  - `POST /api/v1/auth/first-run/create-admins`: Creación obligatoria de los tres administradores segregados (`SysAdmin`, `SecOpsAdmin`, `MlopsAdmin`).
  - `GET /api/v1/brain/status`: Consulta directa del estado del sistema desde `SYSTEM_SOURCE_OF_TRUTH.yaml`.
  - `GET /api/v1/brain/capabilities`: Consulta de la matriz de capacidades de roles.
  - `GET /api/v1/brain/gaps`: Consulta de las brechas registradas y su mitigación.
  - `POST /api/v1/brain/evaluate-proposal`: Evaluación matricial de propuestas de cambio arquitectónico.
  - `POST /api/v1/customs/agent/query`: Consulta agéntica y búsqueda de aranceles en la base ANA de 27,764 códigos con verificación de evidencia.

---

### 3.3 Autenticación, Seguridad y Criptografía WORM (`src/auth/`)
- **`authentication.py` (`AuthenticationEngine`):**
  - Manejo de contraseñas mediante derivación criptográfica PBKDF2-HMAC-SHA256 con 600,000 iteraciones y salt aleatoria de 32 bytes (CSPRNG).
  - Verificación en tiempo constante para evitar ataques de temporización (*timing attacks*).
  - Emisión de tokens de acceso JWT (vigencia: 30 minutos) y Refresh Tokens (vigencia: 7 días con rotación automática).
- **`authorization.py` (`AuthorizationEngine`):**
  - Implementación de RBAC/ABAC con 12 roles y 31 permisos.
  - Evaluación contextual: verifica no solo el rol sino el dominio de la terminal asignada y el tipo de acción.
- **`password_policy.py` (`PasswordPolicy`):**
  - Valida longitud mínima (12 caracteres en producción), entropía de Shannon ($H \ge 3.0$), presencia de mayúsculas, minúsculas, números y caracteres especiales.
  - Verificación contra listas de contraseñas comunes y control de histórico de las últimas 5 contraseñas.
- **`audit.py` (`SecurityAuditLogger`):**
  - Registro inmutable WORM (*Write Once, Read Many*).
  - Cada entrada se encadena criptográficamente con el hash SHA-256 del registro anterior:
    $$H_i = \text{SHA-256}(H_{i-1} \parallel \text{Timestamp} \parallel \text{Actor} \parallel \text{Action} \parallel \text{Payload})$$
  - Provee verificación forense de integridad (`/api/v1/audit/worm/verify`).

---

### 3.4 Plataforma de Datos, Lakehouse Medallion y Aranceles (`src/data/`)
- **Arquitectura Medallion Multi-Fuente:**
  1. **Capa Bronze (`data/bronze/` y `data/raw/`):**
     - Datasets de comercio exterior INEC (`datasets_imports/data/raw/` y `datasets_exports/data/raw/`) con más de 14,500 archivos brutos.
     - Extracciones aduaneras interactivas en `data/bronze/ana_tariff/*.json` con sumas de verificación criptográfica.
     - 353 datasets portuarios oficiales descargados desde `datosabiertos.gob.pa`.
  2. **Capa Silver (`data/silver/`):**
     - Tablas estructuradas Parquet deduplicadas bitemporalmente: `fact_containers.parquet`, `fact_bunkering.parquet`.
     - Series temporales macroeconómicas y energéticas: `fact_macro_energy_multimodal.parquet` (140 meses continuos, telemetría ACP, búnker Platts, tarifas ETESA).
     - Dimensiones aduaneras normalizadas ANA:
       * `dim_ana_hs_catalog.parquet`: Taxonomía y fracciones del Sistema Armonizado.
       * `dim_ana_hs_taxes.parquet`: DAI, ITBMS, ISC e ICCDP.
       * `dim_ana_hs_permits_oga.parquet`: Órganos anuentes (MIDA, MINSA, APA, Energía) y canal SIGA.
       * `dim_ana_hs_trade_agreements.parquet`: TLCs y acuerdos bilaterales con tasas preferenciales.
       * `dim_ana_hs_legal_notes.parquet`: Documentos y notas legales aclaratorias del arancel.
     - Manifiestos criptográficos SHA-256 (`*.parquet.source.json`) garantizan la inmutabilidad de cada tabla Silver.
  3. **Capa Gold (`data/gold/`):** Feature Store consolidado (`panama_national_lakehouse.parquet` y `container_features.parquet`) con 85 variables y cero lookahead bias.
- **`ana_interactive_tariff_scraper.py`:**
  - Motor de extracción contra la API oficial de la ANA (`https://aranceles-api.ana.gob.pa/v1/consulta`).
  - Mapeo completo del DOM de `https://aranceles.ana.gob.pa` (Ionic/Angular SPA), soporte para búsqueda por código HS o término semántico, y normalización relacional hacia las 5 tablas Silver de aranceles.
- **`run_comext_batch_extractor.py`:**
  - Orquestador industrial de comercio exterior para INEC Panamá.
  - Implementa checkpointing estricto (0% redundancia), pacing de cortesía anti-WAF (1.8-3.5s jitter) y detección en DOM de incisos sin movimiento comercial para prevenir timeouts.
- **`ana_hscode_scraper.py` (`PanamaTariffDatabase`):**
  - Base de datos estructurada de subpartidas arancelarias oficiales de la Autoridad Nacional de Aduanas (ANA).
  - Índices de liquidación: DAI, ITBMS (7%), Tasa Administrativa e impuestos específicos.
- **`container_iso6346.py`:**
  - Validador formal de matrículas de contenedores marítimos bajo estándar ISO 6346 utilizando el algoritmo de suma ponderada Módulo-11 con factores de peso $2^i$.

---

### 3.5 Modelos de Machine Learning e Inferencia (`src/models/` y `src/simulation/`)
- **Torneo Multi-Algoritmo (8 Modelos Evaluados):**
  1. **LightGBM Quantile Regressor (Champion):** $\text{WAPE} = 9.11\%$, $R^2 = 0.9594$. Entrenado con Pinball Loss para los cuantiles $\tau \in \{0.10, 0.50, 0.90\}$.
  2. **Random Forest Regressor (Challenger):** $\text{WAPE} = 9.10\%$, $R^2 = 0.9588$.
  3. **CatBoost GBDT (Challenger):** $\text{WAPE} = 9.24\%$, $R^2 = 0.9581$.
  4. **Extra Trees Regressor (Challenger):** $\text{WAPE} = 9.35\%$, $R^2 = 0.9572$.
  5. **HistGradientBoosting (Challenger):** $\text{WAPE} = 9.78\%$, $R^2 = 0.9545$.
  6. **Quantile Neural MLP:** $\text{WAPE} = 11.20\%$, $R^2 = 0.9310$.
  7. **Bayesian Ridge Regression:** $\text{WAPE} = 14.85\%$, $R^2 = 0.8850$.
  8. **Ridge / ElasticNet (Baseline Lineal):** $\text{WAPE} > 1900\%$ (colapso teórico ante multicolinealidad severa).
- **Motor de Simulación Monte Carlo (`monte_carlo_engine.py`):**
  - Generación de choques multivariados correlacionados mediante la descomposición de Cholesky de la matriz de covarianza empírica $\mathbf{\Sigma} = \mathbf{L} \mathbf{L}^T$.
  - Modelado de eventos catastróficos mediante el proceso de Salto-Difusión de Merton (Poisson Jumps):
    $$\frac{dS_t}{S_{t^-}} = \mu dt + \sigma dW_t + J_t dN_t$$
  - Métricas de riesgo: Value at Risk (VaR 95% / 99%) y Conditional VaR (Expected Shortfall).

---

## 4. ANÁLISIS EXHAUSTIVO DE LAS INTERFACES DE USUARIO (UI/UX)

El proyecto cuenta con dos superficies web principales:
1. **La Landing Institucional (`landing.html`):** Accesible en `http://127.0.0.1:8000/`.
2. **La Estación de Mando y Dashboard (`index.html`):** Accesible en `http://127.0.0.1:8000/app`.

---

### 4.1 Landing Institucional (`landing.html` + `portal.js`)
- **Paleta de Colores y Estilo:**
  - Fondo primario: Deep Marine (`#081420` a `#102a3e`).
  - Textos: Blanco perla (`#edf5ff`) y azul tenue (`#94a3b8`).
  - Bordes y líneas: Cian tecnológico (`#2a5368`).
- **Componentes y Comportamiento al Clic:**
  - **Selector de Idioma (`.language-select`):** Conmuta instantáneamente la interfaz entre Español (ES), Inglés (EN) y Portugués (PT) almacenando la preferencia en `localStorage.getItem('amp-locale')`.
  - **Botón "Abrir mi instancia ↗" / "Explorar mi instancia →":** Redirige a `/app` abriendo la aplicación principal.
  - **Sección "LOOP ENGINEERING":** Despliega el acordeón con los cuatro pasos del ciclo: *Observar $\rightarrow$ Implementar $\rightarrow$ Verificar $\rightarrow$ Aprender*.
  - **Botón de Modo Oscuro/Claro (`[data-theme-toggle]`):** Conmuta la variable de tema global vía `theme.js`.

---

### 4.2 Dashboard y Estación de Operaciones (`index.html` + `static/js/app.js`)

#### A. Barra Superior de Navegación y HUD de Seguridad
- **Logo del Proyecto:** SVG oficial con enlaces a la documentación.
- **Badges de Telemetría en Vivo:**
  - `health-badge`: Muestra el estado del Gateway y la conectividad con el backend (`OPERATIVO`).
  - `latency-badge`: Latencia de inferencia en tiempo real (ej. `12.4 ms`).
  - `algo-badge`: Algoritmo activo (`LightGBM Quantiles`).
- **Botón de Autenticación IAM (`#btn-auth-iam`):**
  - *Acción:* Abre el modal de autenticación (`#auth-iam-modal`).
  - *Comportamiento:* Permite iniciar sesión, ver claims del JWT, roles asignados y cerrar sesión.

#### B. Pestaña 1: Pronóstico Operacional de Demanda Portuaria (`#tab-forecast`)
- **Selectores de Entrada:**
  - `port-select`: Selección de terminal (`Puerto Balboa`, `SSA Marine MIT`, `Puerto Cristóbal`, etc.).
  - `algo-select`: Elección de algoritmo (Champion LightGBM, Random Forest, etc.).
  - `horizon-slider`: Rango de 1 a 6 meses.
  - `bunker-slider` y `trans-slider`: Inyección de perturbaciones What-If (desviación porcentual de combustible y trasbordo).
- **Botón "Ejecutar Pronóstico" (`#btn-predict`):**
  - *Flujo y Manejo de Triggers:*
    1. Se deshabilita inmediatamente el botón (`btnPredict.disabled = true`) para prevenir race conditions (UI-008).
    2. Se emite un request `POST /predict`.
    3. Si la respuesta es exitosa:
       - Actualiza los KPIs visuales: `kpi-p50` (TEUs proyectados), `kpi-p10` y `kpi-p90`.
       - Renderiza el gráfico interactivo Chart.js con la banda sombreada de incertidumbre.
       - Llena la tabla de detalle mensual `forecast-tbody`.
    4. En el bloque `finally`, se rehabilita el botón.

#### C. Pestaña 2: Simulación Estocástica de Riesgo Monte Carlo (`#tab-simulation`)
- **Selectores:**
  - `sim-port-select`: Puerto a evaluar.
  - `sim-scenario-select`: Escenario de shock (`Sequía Severa Lago Gatún`, `Alza de Búnker +25%`, `Huelga Portuaria 15 días`).
  - `sim-paths-slider`: Número de trayectorias (1,000 a 10,000).
- **Botón "Lanzar Simulación" (`#btn-run-sim`):**
  - *Acción:* Llama a `POST /simulate`.
  - *Resultado:* Calcula y muestra el VaR 95%, CVaR, distribución de densidad empírica y sella la ejecución en el libro mayor inmutable WORM con su respectivo `audit_hash`.

#### D. Pestaña 3: Asistente Agéntico y Aranceles Aduaneros ANA (`#tab-customs`)
- **Input de Consulta (`#agent-query-input`):** Campo de texto libre para descripciones de mercancías o códigos arancelarios.
- **Botón "Consultar Agente" (`#btn-run-agent`):**
  - *Máquina de Estados Finita Determinista (Corrección UI-001):*
    - **Paso 1:** Validación y Guardrails (`Evaluando dominios admisibles...`).
    - **Paso 2:** Recuperación RAG de Evidencia (`Buscando en 27,764 partidas ANA...`).
    - **Paso 3:** Inferencia y Deducción Legal (`Calculando DAI, ITBMS y tratados...`).
    - **Paso 4:** Sello Criptográfico (`Sellando con HMAC-SHA256...`).
    - *Comportamiento ante Rechazo:* Si el Paso 1 es bloqueado por los guardrails, los Pasos 2, 3 y 4 pasan inmediatamente y de manera determinista al estado `OMITTED`, eliminando spinners congelados.
    - *Traza de Auditoría (Corrección UI-003):* En lugar de CoT privado, expone la traza verificable de reglas y evidencia legal consultada con botón de copia de `trace_id` (UI-007).

#### E. Asistente de Primer Inicio Obligatorio (`#first-run-setup-modal`)
- **Comportamiento Crítico de Seguridad:**
  - Se activa si `GET /api/v1/auth/first-run/status` retorna `requires_first_run_setup: true`.
  - Bloquea cualquier interacción administrativa hasta:
    1. Cambiar la contraseña temporal del usuario `root` (`POST /api/v1/auth/first-run/change-root-password`).
    2. Crear los administradores segregados: `SysAdmin`, `SecOpsAdmin` y `MlopsAdmin` (`POST /api/v1/auth/first-run/create-admins`).
  - Una vez completado, el modal se cierra y almacena el estado seguro en la base de datos empresarial.

---

## 5. TRAZABILIDAD, AUDITORÍA Y TELEMETRÍA DE ACCIONES

Cada interacción dentro de la plataforma genera una traza verificable:
1. **Identificador Global de Solicitud (`request_id` / `trace_id`):** Formato `req_<hex_16>`. Generado en el Gateway Go o en FastAPI y devuelto en las cabeceras HTTP `X-Request-ID`.
2. **Sello Criptográfico de Respuesta (`cryptographic_seal`):** Hash HMAC-SHA256 calculado sobre el contenido canónico de la respuesta y firmado con la llave interna del nodo.
3. **Telemetría de Uso (`src/serving/v1_router.py`):**
   - Registro de tiempo de inferencia en microsegundos.
   - Conteo de tokens de entrada y salida para consultas agénticas.
   - Endpoint de feedback MLOps (`POST /api/v1/telemetry/feedback`) para registrar calificaciones de usuarios (1-5 estrellas, 👍/👎 y comentarios técnicos) vinculado al `trace_id`.

---

## 6. MATRIZ DE CAPACIDADES Y ROLES (RBAC)

El sistema define 12 roles oficiales y 31 permisos gestionados en `project_brain/CAPABILITY_MATRIX.yaml`:

| Rol | Identificador | Capacidades Clave | Restricciones |
| :--- | :--- | :--- | :--- |
| **Super Administrador** | `superadmin` / `root` | Acceso total (`*`), rotación de secretos, gestión de llaves y usuarios | Requiere MFA en producción |
| **Administrador MLOps** | `admin` | Despliegue de modelos, ajuste de guardrails, lectura de auditoría | No rota secretos maestros ni altera el Brain |
| **Ingeniero de ML** | `ml_engineer` | Entrenamiento de modelos, feature store, lakehouse, simulaciones | No despliega modelos a producción |
| **Oficial de Aduanas** | `customs_officer` | Consulta de aranceles ANA, notas marginales, acuerdos comerciales | Solo lee sus propias consultas de auditoría |
| **Analista Portuario** | `port_analyst` | Pronósticos de TEUs, agregados del lakehouse, simulaciones | Sin acceso a gestión de modelos ni usuarios |
| **Auditor Soberano** | `auditor` | Verificación forense WORM, inspección de trazas y sellos | Acceso de solo lectura en todo el sistema |

---

## 7. MATRIZ DE PRUEBAS AUTOMATIZADAS Y SUITE DE VERIFICACIÓN

El repositorio cuenta con 90 archivos de prueba automatizada bajo `tests/` que validan el 100% de los contratos del sistema:
- `test_security_gateway.py`: Valida cabeceras HSTS, CSP y proxy del Gateway Go.
- `test_ui_state_machine.py`: Valida la máquina de estados determinista y los estados `OMITTED`.
- `test_brain_api.py`: Valida que los endpoints `/api/v1/brain/*` lean correctamente `project_brain/`.
- `test_first_run_auth.py`: Valida el cambio de contraseña de root y creación de administradores.
- `test_features.py`: Valida el cálculo de las 85 características sin fuga temporal.
- `test_simulation.py`: Valida Cholesky, saltos de Merton y cálculo de VaR/CVaR.
- `test_tariff_historical_search.py`: Valida la base arancelaria de 27,764 registros.

---

## 8. CONCLUSIONES Y HOJA DE RUTA OPERATIVA

1. **Estado de Producción:** El proyecto se encuentra actualmente en estado **`PRODUCTION_CANDIDATE`**. Su promoción formal a `PRODUCTION_VERIFIED` requiere completar el ciclo de cierre LOOP documentado en `project_brain/GAP_REGISTER.yaml`.
2. **Soberanía y Transparencia:** La arquitectura cumple con los más altos estándares de reproducibilidad científica (semilla fija 42, zero lookahead bias, datos reales de la AMP y cero código cerrado).
3. **Mantenibilidad:** La separación entre el Gateway Go (red/seguridad) y FastAPI (computación analítica) garantiza una latencia mínima y máxima resiliencia operativa en cualquier sistema operativo host o clúster Kubernetes.

---
*Fin del Mapa Técnico y Documento de Auditoría Integral.*  
*developed by Ing. Miguel Antonio Benítez González (UTP) • Panamá, 2026.*
