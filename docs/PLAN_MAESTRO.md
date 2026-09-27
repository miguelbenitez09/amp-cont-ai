<USER_REQUEST>
/goal  Debes verificar que se implemente: # amp-cont-ai — Plan Maestro de Modernización

## Transformación de Panamá PortOps-AI en un Framework MLOps Open Source para Modelos, Datos, Inferencia, Agentes y MCP

### 1. Objetivo de la transformación

El repositorio debe dejar de ser una aplicación monolítica orientada exclusivamente a analítica portuaria y pasar a ser un **framework MLOps modular, reproducible y extensible**, capaz de administrar:

* modelos clásicos de Machine Learning;
* modelos Deep Learning;
* LLMs y VLMs;
* embeddings y rerankers;
* modelos propios entrenados desde cero;
* modelos descargados de Hugging Face;
* modelos desplegados mediante vLLM;
* modelos locales mediante otros runtimes compatibles;
* modelos expuestos mediante APIs OpenAI-compatible;
* artefactos registrados en almacenamiento S3/MinIO;
* evaluaciones y benchmarks;
* pipelines de entrenamiento;
* despliegues;
* agentes;
* MCP servers;
* tools;
* Souls/agent profiles;
* permisos por usuario, rol y modelo;
* auditoría y observabilidad.

**Panamá PortOps-AI debe convertirse en un paquete de dominio**, no en el núcleo arquitectónico.

La arquitectura conceptual pasa a ser:

```text
                    ┌─────────────────────────────┐
                    │       MLOps Control Plane    │
                    │                              │
                    │ IAM / RBAC / Policies       │
                    │ Model Catalog                │
                    │ Model Registry               │
                    │ Runtime Manager              │
                    │ Deployments                  │
                    │ Evaluation                   │
                    │ Data Catalog                 │
                    │ MCP / Tools                  │
                    │ Agents / Souls               │
                    │ Audit / Observability        │
                    └─────────────┬───────────────┘
                                  │
          ┌───────────────────────┼────────────────────────┐
          │                       │                        │
      vLLM Runtime            ML Runtime              RAG Runtime
          │                       │                        │
     LLM / VLM              LightGBM / RF         Embeddings / Vector
          │                       │                        │
          └───────────────────────┼────────────────────────┘
                                  │
                       Artifact / Model Store
                         MinIO / S3 / Registry
                                  │
                       Dataset / Lakehouse
                      Bronze → Silver → Gold
                                  │
                      Domain Packs / Plugins
                   ┌──────────────┴─────────────┐
                   │                            │
             PortOps Pack                 Otro proyecto
```

---

# 2. Principio arquitectónico fundamental

Debe existir una separación estricta entre:

### A. Model Registry

Representa modelos que existen como artefactos MLOps.

Ejemplos:

```text
portops-teu-forecast
lightgbm-container-demand
qneural-teu-quantile
my-custom-transformer
my-gemma-finetune
company-vision-model
```

### B. Runtime Model Catalog

Representa modelos realmente disponibles para ser servidos por un runtime.

Ejemplos:

```text
google/gemma-4-...
meta-llama/...
Qwen/...
mistralai/...
local/my-model
```

### C. Benchmark Catalog

Representa resultados comparativos.

Ejemplo:

```text
experiment_id
dataset_version
split_strategy
model_version
WAPE
MAE
RMSE
R2
latency
throughput
memory
```

### D. Model Access Catalog

Define quién puede usar cada modelo.

### E. Model Deployment Catalog

Representa qué modelo está ejecutándose, dónde y bajo qué configuración.

Nunca volver a utilizar un mismo JSON/diccionario para representar las cinco cosas anteriores.

---

# 3. Corrección inmediata del problema de los dropdowns

El dropdown actual no debe contener nombres escritos manualmente.

Debe evolucionar de:

```html
<select id="algo-select">
    <option value="ensemble">...</option>
    <option value="random_forest">...</option>
</select>
```

a:

```text
GET /api/v1/models/catalog
```

y el frontend debe construir el selector a partir de esa respuesta.

La interfaz deberá mostrar únicamente modelos que cumplan:

```text
discoverable = true
status       = AVAILABLE
health       = HEALTHY
access       = ALLOWED
runtime      = compatible
```

---

# 4. Nuevo Model Catalog Service

Crear:

```text
src/platform/models/catalog/
```

con:

```text
catalog_service.py
catalog_repository.py
catalog_sync.py
catalog_normalizer.py
catalog_filters.py
catalog_health.py
catalog_sources/
    vllm.py
    huggingface.py
    local_registry.py
    mlflow.py
    filesystem.py
```

El modelo normalizado debe contener como mínimo:

```yaml
model_id:
display_name:
namespace:
source:
source_uri:
revision:
commit_sha:
license:
gated:
pipeline_task:
architecture:
parameter_count:
dtype:
quantization:
context_length:
input_modalities:
output_modalities:
supports_chat:
supports_tools:
supports_vision:
supports_embeddings:
runtime_compatibility:
artifact_uri:
artifact_hash:
registry_status:
deployment_status:
health_status:
created_at:
updated_at:
metadata:
```

---

# 5. Fuentes reales del catálogo

## 5.1 Modelos servidos por vLLM

La plataforma debe interrogar el runtime real.

Conceptualmente:

```text
GET {VLLM_BASE_URL}/models
```

y utilizar la respuesta como fuente de modelos actualmente servidos.

No asumir:

```text
DEFAULT_VLLM_MODEL
```

como prueba de existencia.

El sistema debe diferenciar:

```text
Configured
Discovered
Loaded
Healthy
Serving
```

Un modelo configurado pero no cargado **no debe aparecer como disponible para inferencia**.

vLLM mantiene un servidor compatible con la interfaz de APIs OpenAI y su documentación actual contempla además configuración de tool calling y parsers específicos por modelo.

---

# 6. Catálogo Hugging Face

El framework debe tener un conector independiente:

```text
HuggingFaceCatalogProvider
```

Capaz de:

```text
search
filter
inspect
validate
import
compare
register
```

Filtros:

```text
author
task
pipeline
library
parameters
license
gated
quantization
downloads
likes
runtime
architecture
context
language
multimodal
tool-calling
```

La API de Hugging Face permite listar modelos y aplicar filtros por tarea, autor, número de parámetros y biblioteca, además de consultar metadatos de modelos.

La UI deberá incorporar:

```text
Buscar modelos
        ↓
Aplicar filtros
        ↓
Ver detalles
        ↓
Compatibility Check
        ↓
Importar al Registry
        ↓
Validar
        ↓
Crear Deployment
```

No se debe instalar un modelo directamente desde una tarjeta sin pasar por validación.

---

# 7. Tipos de modelos

El selector actual mezcla algoritmos estadísticos con LLMs.

Esto debe eliminarse.

Crear categorías:

```text
MODEL_TYPE

forecasting
classification
regression
ranking
embedding
reranker
llm
vlm
speech
vision
multimodal
anomaly_detection
time_series
generative
custom
```

Por ejemplo:

```text
Modelo Predictivo
    LightGBM
    Random Forest
    CatBoost

Foundation Model
    Gemma
    Llama
    Qwen
    Mistral

Embedding
    BGE
    E5
    GTE

Reranker
    BGE Reranker
    Cohere-compatible
```

El selector de inferencia debe presentar solamente modelos compatibles con la operación seleccionada.

---

# 8. Model Registry real

Crear:

```text
src/platform/registry/
```

Esquema conceptual:

```text
model
model_version
model_artifact
model_parameter
model_signature
model_dataset
model_evaluation
model_lineage
model_deployment
model_alias
model_approval
model_access_policy
```

Ciclo de vida:

```text
DRAFT
  ↓
TRAINED
  ↓
VALIDATED
  ↓
EVALUATED
  ↓
REVIEW
  ↓
APPROVED
  ↓
STAGED
  ↓
DEPLOYED
  ↓
SERVING
  ↓
DEPRECATED
  ↓
ARCHIVED
```

Cada promoción debe tener:

```text
actor
timestamp
model_version
source_commit
dataset_version
evaluation_id
approval_id
artifact_hash
deployment_manifest
```

---

# 9. Model Versioning

Nunca utilizar solamente:

```text
model_name
```

Debe existir:

```text
model_id
version
revision
artifact_hash
```

Ejemplo:

```text
portops-teu-forecast
version: 2.4.1
git_commit: 9a81...
dataset: amp-2026-09
artifact_sha256: ...
```

Alias:

```text
champion
production
staging
candidate
```

Los aliases no deben almacenar modelos; deben apuntar a versiones.

---

# 10. Despliegue real de vLLM

Separar:

```text
Model
Deployment
Runtime
Instance
```

Ejemplo:

```yaml
deployment:
  id: dep_001

runtime:
  type: vllm
  version: x.y.z
  image_digest: sha256:...

model:
  source: huggingface
  id: google/...
  revision: ...

serving:
  served_model_name: portops-gemma
  port: 8000

compute:
  device: cuda
  gpu_memory_utilization: 0.88
  tensor_parallel_size: 1
  max_model_len: 8192

security:
  authentication: bearer
  public_access: false

tools:
  enabled: true

health:
  readiness_timeout_seconds: 120
```

Nada crítico debe vivir simultáneamente en:

```text
.env
docker-compose.yml
Python
HTML
JavaScript
database
```

Debe existir una sola configuración canónica.

---

# 11. Declaración vs realidad de vLLM

La plataforma necesita una pantalla:

## Deployment Verification

No debe decir:

```text
vLLM Configured ✅
```

solamente porque existe un bloque Docker.

Debe ejecutar:

### Check 1

GPU detectable.

### Check 2

CUDA funcional.

### Check 3

Docker GPU runtime funcional.

### Check 4

Imagen vLLM descargable.

### Check 5

Modelo descargable.

### Check 6

Artifact hash válido.

### Check 7

Container iniciado.

### Check 8

Health endpoint válido.

### Check 9

`/v1/models` devuelve el modelo esperado.

### Check 10

Chat completion funciona.

### Check 11

Token streaming funciona.

### Check 12

Tool calling funciona cuando está habilitado.

### Check 13

Modelo devuelto por `/v1/models` coincide con el Registry.

### Check 14

Authentication policy coincide con el gateway.

### Check 15

Métricas llegan a observabilidad.

Resultado:

```text
CONFIGURED
READY
HEALTHY
SERVING
DEGRADED
FAILED
```

---

# 12. El runtime debe poder verificarse automáticamente

Crear:

```text
runtime_probe.py
vllm_probe.py
ollama_probe.py
openai_compatible_probe.py
```

Cada probe devuelve:

```json
{
  "runtime": "vllm",
  "reachable": true,
  "version": "...",
  "models": [...],
  "gpu": {...},
  "tool_calling": true,
  "latency_ms": 42.1,
  "status": "HEALTHY"
}
```

Eso alimentará directamente el catálogo.

---

# 13. Nueva interfaz principal

El frontend actual es demasiado monolítico. El archivo `index.html` contiene miles de líneas de UI y `app.js` miles de líneas de lógica, además de una segunda estación Streamlit.

Migrar a:

```text
frontend/
    src/
        app/
        components/
        layouts/
        pages/
        features/
            models/
            deployments/
            datasets/
            evaluations/
            users/
            mcp/
            agents/
            security/
            glossary/
        services/
        api/
        store/
        hooks/
        types/
        styles/
```

Recomiendo:

```text
React
TypeScript
Vite
```

o, si se quiere minimizar dependencias:

```text
Web Components
TypeScript
Vite
```

Streamlit debe quedar como:

```text
research/
experiments/
notebooks/
```

y no como segundo control plane.

---

# 14. Nueva navegación

La aplicación debe tener:

```text
Overview

Models
 ├─ Catalog
 ├─ Registry
 ├─ Versions
 ├─ Evaluations
 └─ Deployments

Datasets
 ├─ Catalog
 ├─ Sources
 ├─ Lineage
 ├─ Quality
 └─ Privacy

Inference
 ├─ Playground
 ├─ Runtime Status
 ├─ Requests
 └─ Usage

Agents
 ├─ Souls
 ├─ Agents
 ├─ Tools
 ├─ MCP Servers
 └─ Access Requests

MLOps
 ├─ Experiments
 ├─ Training Runs
 ├─ Benchmarks
 ├─ Pipelines
 └─ Artifacts

Security
 ├─ Users
 ├─ Roles
 ├─ Sessions
 ├─ Policies
 ├─ Wazuh
 └─ Audit

Administration
 ├─ Runtime Configuration
 ├─ Storage
 ├─ Secrets
 ├─ Integrations
 └─ System Health

Education
 ├─ Glossary
 ├─ ML Concepts
 ├─ Formulas
 ├─ Practical Examples
 └─ Architecture Guide
```

---

# 15. Home `/`

La página inicial debe conservar la identidad Deep Marine, pero convertirse en un verdadero portal de proyecto.

Orden:

```text
Hero
↓
¿Qué es amp-cont-ai?
↓
¿Por qué existe?
↓
Arquitectura
↓
Stack tecnológico
↓
9 fases MLOps
↓
Datos utilizados
↓
Model Registry
↓
Inference / vLLM
↓
Agents / MCP
↓
Security
↓
Reproducibilidad
↓
Licencia
↓
Disclaimers
↓
Entrar al Control Plane
```

La home no debe ejecutar inferencias administrativas ni depender de un modelo concreto.

---

# 16. Primer arranque

El bootstrap debe convertirse en:

```text
FIRST_RUN
```

Flujo:

```text
1. Verificar instalación
2. Crear Root Owner
3. Generar credenciales temporales
4. Obligar cambio de contraseña
5. Configurar MFA
6. Crear roles
7. Configurar almacenamiento
8. Configurar runtime
9. Detectar GPU
10. Detectar vLLM
11. Configurar Model Catalog
12. Ejecutar Health Checks
13. Ejecutar Security Checks
14. Ejecutar Data Checks
15. Finalizar instalación
```

El actual `bootstrap.py` posee un fallback de contraseña predeterminada y genera un archivo de credenciales; eso debe sustituirse por un flujo de bootstrap verdaderamente administrado.

---

# 17. Root Owner

El Root Owner debe ser el máximo nivel del sistema.

Puede:

```text
crear/eliminar usuarios
crear/modificar roles
asignar permisos
habilitar/deshabilitar modelos
hacer público un modelo
cambiar políticas de inferencia
aprobar deployments
aprobar tools críticas
configurar MCP
configurar Wazuh
administrar almacenamiento
administrar runtimes
revocar sesiones
revocar tokens
ver auditoría
```

No debe utilizarse como usuario operacional cotidiano.

---

# 18. Roles recomendados

```text
root_owner
platform_admin
mlops_admin
mlops_engineer
model_reviewer
data_steward
security_admin
agent_admin
operator
researcher
auditor
viewer
```

Cada rol debe contener:

```text
permissions
allowed_models
allowed_runtimes
allowed_tools
allowed_data_domains
rate_limits
token_limits
environment_access
```

---

# 19. No utilizar únicamente RBAC

La autorización debe ser:

```text
RBAC
+
ABAC
+
Resource Policies
+
Runtime Policies
```

Ejemplo:

```text
Usuario:
    miguel

Rol:
    mlops_engineer

Modelo:
    internal/gemma-portops

Entorno:
    production

Acción:
    inference

Resultado:
    ALLOW
```

Pero:

```text
Usuario:
    researcher

Modelo:
    private/llama-enterprise

Resultado:
    DENY
```

aunque ambos posean cierto rol.

---

# 20. Política de acceso al modelo

Crear entidad:

```text
model_access_policy
```

Opciones:

```text
PUBLIC
REGISTERED
VERIFIED
ROLE_RESTRICTED
USER_RESTRICTED
PRIVATE
```

Esto debe ser independiente de la existencia del modelo.

Ejemplo:

```yaml
model_id: internal/gemma-portops
access_policy:
  mode: VERIFIED
  allowed_roles:
    - operator
    - researcher
    - mlops_engineer
```

---

# 21. Política pública

Cuando el administrador seleccione:

```text
Modelo público
```

la interfaz debe mostrar:

```text
⚠ Esto permite inferencia sin autenticación.

Rate limit
Per-IP limit
Token budget
Max request size
Allowed operations
Tool access
Data access
Audit mode
```

La publicación de un modelo debe requerir:

```text
Root Owner
+
confirmation
+
audit event
```

Nunca debe hacerse público un modelo simplemente porque está desplegado.

---

# 22. Gestión de usuarios

Nueva pantalla:

## Users

Tabla:

```text
Username
Name
Email
Status
Verification
MFA
Roles
Models
Tools
Last Login
Created
Actions
```

Acciones:

```text
View
Edit
Disable
Reset MFA
Reset Sessions
Assign Roles
Assign Models
Assign Tools
View Audit
```

Formulario de usuario:

```text
Identity
Credentials
MFA
Roles
Model Access
Tool Access
Data Access
Rate Limits
Status
Audit
```

---

# 23. Model Access Matrix

La interfaz debe tener una matriz:

| Usuario/Rol | Modelo | Inference | Streaming |      Tools | Fine-tune | Deploy |
| ----------- | ------ | --------: | --------: | ---------: | --------: | -----: |
| root        | Gemma  |         ✓ |         ✓ |          ✓ |         ✓ |      ✓ |
| mlops       | Gemma  |         ✓ |         ✓ |          ✓ |         ✓ |      ✓ |
| operator    | Gemma  |         ✓ |         ✓ |   limitado |         ✗ |      ✗ |
| researcher  | Gemma  |         ✓ |         ✓ | solicitado |         ✗ |      ✗ |
| viewer      | Gemma  |         ✗ |         ✗ |          ✗ |         ✗ |      ✗ |

Esta matriz debe ser una visualización de las políticas reales, no HTML estático.

---

# 24. API Tokens

Cada usuario podrá tener:

```text
Personal Access Token
Service Token
Agent Token
MCP Token
Runtime Token
```

Cada token:

```text
token_id
owner
scope
expires_at
created_at
last_used
revoked_at
ip_policy
model_policy
tool_policy
```

Nunca almacenar tokens en texto plano.

---

# 25. Corrección criptográfica

No implementar mecanismos como:

```text
XOR + Base64
static salt
hard-coded master secrets
```

como sistema de cifrado.

Debe existir:

```text
OS environment
Docker secrets
Kubernetes Secrets
Vault
SOPS + age
```

según despliegue.

La clave maestra nunca debe estar en Git.

---

# 26. MCP Registry

Crear:

```text
mcp_servers
mcp_tools
mcp_resources
mcp_prompts
mcp_connections
mcp_credentials
mcp_tests
```

Cada MCP server debe tener:

```yaml
id:
name:
version:
transport:
endpoint:
authentication:
protocol_version:
capabilities:
status:
last_health_check:
```

---

# 27. Verificación MCP

Al registrar un MCP:

```text
1. Validate endpoint
2. Authenticate
3. initialize
4. negotiate protocol
5. tools/list
6. resources/list
7. prompts/list
8. schema validation
9. latency test
10. error test
11. permission test
12. sandbox test
```

Debe aparecer:

```text
CONNECTED
DEGRADED
AUTH_FAILED
PROTOCOL_ERROR
UNTRUSTED
BLOCKED
```

---

# 28. Tools

La herramienta actual contiene schemas estáticos y una función central que despacha mediante `if/elif`.

Sustituir:

```text
if name == "..."
elif name == "..."
```

por:

```text
ToolRegistry
ToolDefinition
ToolExecutor
ToolPolicy
ToolValidator
ToolAudit
```

Ejemplo:

```yaml
tool:
  id: get_port_forecast

  risk:
    level: LOW

  input_schema:
  output_schema:

  permissions:
    - forecast.read

  models:
    - portops-teu-forecast

  approval:
    required: false
```

---

# 29. Tool Access Request

Toda tool de riesgo medio/alto debe pasar por:

```text
REQUESTED
↓
VALIDATING
↓
PENDING_APPROVAL
↓
APPROVED / DENIED
↓
EXECUTING
↓
COMPLETED / FAILED
↓
AUDITED
```

La solicitud debe registrar:

```text
request_id
user
agent
soul
model
tool
arguments
requested_at
risk
approval_required
approver
decision
decision_reason
execution_time
result_hash
```

Las herramientas críticas nunca deben ejecutar directamente desde `tools/call` sin que la policy engine decida.

---

# 30. Souls

Las Souls no deben ser simples strings con hashes.

Crear:

```text
Soul
SoulVersion
SoulPolicy
SoulToolBinding
SoulKnowledgeBinding
SoulModelBinding
SoulApprovalPolicy
```

Ejemplo:

```yaml
id: auditor_maritimo

version: 3

objective:
  compliance_analysis

model_constraints:
  allowed_models:
    - gemma-portops

tools:
  allow:
    - query_maritime_knowledge
    - get_port_forecast

actions:
  require_approval:
    - export_data
    - modify_config
```

El hash debe verificar integridad, pero no debe etiquetarse como “cifrado”.

---

# 31. Agentes

Separar:

```text
Agent Identity
Agent Definition
Soul
Model
Tools
Memory
Knowledge
Policies
Execution
```

Un agente debe poder cambiar de modelo sin cambiar su identidad.

Ejemplo:

```text
Auditor Agent
       │
       ├── Soul
       ├── Model: Gemma
       ├── Tools
       ├── RAG
       └── Policy
```

---

# 32. Modelo → Agente → Tool

La autorización debe comprobar:

```text
User
 ↓
Role
 ↓
Agent
 ↓
Soul
 ↓
Model
 ↓
Tool
 ↓
Resource
 ↓
Action
```

No:

```text
Model → execute_tool()
```

---

# 33. Data Platform

Mantener Medallion:

```text
Bronze
Silver
Gold
```

pero agregar:

```text
Data Catalog
Data Contract
Data Quality
Data Lineage
Data Provenance
Data Classification
Privacy
Retention
```

Cada dataset debe tener:

```yaml
dataset_id:
name:
source:
official_source:
license:
owner:
extraction_time:
validity_period:
published_at:
schema_version:
record_count:
checksum:
privacy_classification:
processing_pipeline:
```

---

# 34. Corrección de la anonimización

El repositorio describe HMAC-SHA256 como anonimización irreversible. El diseño nuevo debe distinguir:

```text
Raw
↓
Sensitive
↓
Pseudonymized
↓
Anonymized
↓
Aggregated
```

HMAC con una clave secreta debe documentarse como **pseudonimización**, no automáticamente como anonimización.

El pipeline debe declarar:

```text
technique
key dependency
re-identification risk
data owner
purpose
retention
```

---

# 35. Datos reales vs datos demostrativos

Cada objeto debe tener:

```text
DATA_STATUS

OFFICIAL
VERIFIED
DERIVED
SIMULATED
SYNTHETIC
DEMO
UNVERIFIED
```

La UI debe impedir que:

```text
SIMULATED
```

aparezca con un badge:

```text
REAL
```

Este cambio es fundamental para el principio Zero Mocks.

---

# 36. Eliminación de métricas ficticias

Eliminar definitivamente valores escritos como:

```text
248 inference
42,850 tokens
98.4%
42 reviews
218500 TEUs
+35.50%
```

cuando no procedan de una ejecución real.

La interfaz debe mostrar:

```text
No data
Not measured
Awaiting execution
```

en lugar de inventar cifras.

---

# 37. Benchmark real

`ChampionSuite` debe dejar de ser una tabla codificada.

Crear:

```text
Experiment
Run
Model
Dataset
Split
Metric
Result
Artifact
Environment
```

Un benchmark se crea así:

```text
Dataset v10
        ↓
Split strategy
        ↓
Train
        ↓
Evaluate
        ↓
Metrics
        ↓
Store
        ↓
Compare
        ↓
Candidate
```

El estado Champion debe ser derivado de una regla de selección registrada, no escrito a mano.

---

# 38. Champion / Challenger

Debe existir:

```text
selection_policy
```

Ejemplo:

```yaml
objective:
  primary_metric: WAPE
  minimize: true

constraints:
  max_latency_ms: 100
  min_r2: 0.90

tie_breaker:
  - latency
  - memory
```

Por lo tanto, el sistema puede decir:

```text
Selected candidate according to policy X
```

en vez de asumir:

```text
LightGBM Champion
```

por código.

---

# 39. Nueve fases MLOps

La home y módulo educativo deben explicar:

### Fase 1 — Data Acquisition

Fuentes, ingesta y provenance.

### Fase 2 — Data Engineering

Bronze/Silver/Gold.

### Fase 3 — Data Quality

Schema, nulls, outliers, temporalidad.

### Fase 4 — Feature Engineering

Features, transformaciones, leakage control.

### Fase 5 — Training

Algoritmos, hiperparámetros, experimentos.

### Fase 6 — Evaluation

Benchmark, backtesting, calibración.

### Fase 7 — Registry

Versioning, lineage, approvals.

### Fase 8 — Deployment

Docker, runtime, GPU, vLLM, Kubernetes.

### Fase 9 — Monitoring & Governance

Drift, latency, security, Wazuh, audit, retraining.

---

# 40. Glosario pedagógico

El módulo actual debe convertirse en una plataforma educativa.

Cada término debe tener:

```text
Definition
Simple explanation
Technical explanation
Formula
Variables
Example
Python implementation
Real-world use case
Common mistake
When not to use
Related concepts
Source
```

Ejemplo:

```text
Epoch

Simple:
Una pasada completa del dataset...

Technical:
Número de iteraciones...
```

Luego:

```text
Formula
↓
Visual
↓
Dataset example
↓
Python
↓
Result
```

---

# 41. Fórmulas

No mostrar fórmulas como bloques aislados.

Cada fórmula debe estar acompañada de:

```text
Nombre
Objetivo
Variables
Dimensión
Supuestos
Derivación
Interpretación
Código
Ejemplo numérico
```

El frontend debe renderizar KaTeX desde el stack versionado del propio proyecto para facilitar instalaciones offline y reproducibles, en vez de depender del CDN de JS/CSS que actualmente usa la página.

---

# 42. Documentación de scripts

Cada script debe tener una ficha:

```text
script
purpose
inputs
outputs
dependencies
environment variables
side effects
idempotency
failure modes
examples
tests
```

Ejemplo:

```text
scripts/train_reproducible.py

Purpose:
Entrenar versión reproducible del modelo.

Input:
dataset_version
model_config
seed

Output:
artifact
metrics
manifest
hash
```

---

# 43. Exportación de resultados

Todo experimento debe poder exportarse:

```text
JSON
CSV
Parquet
HTML report
Machine-readable manifest
```

Cada exportación debe contener:

```text
run_id
model_version
dataset_version
parameters
environment
seed
metrics
artifact_hash
timestamp
source_commit
```

---

# 44. Model Playground

Crear una interfaz de prueba real:

```text
Model
Runtime
Prompt
Parameters
Streaming
Tools
RAG
Temperature
Top P
Max Tokens
System Prompt
```

Antes de ejecutar:

```text
Authorization Check
Model Health Check
Quota Check
Tool Policy Check
Data Policy Check
```

Después:

```text
Latency
TTFT
tokens/sec
input tokens
output tokens
total tokens
model
runtime
request ID
tool calls
sources
```

---

# 45. Runtime selector

En lugar de:

```text
vllm
ollama
openai
gemini
anthropic
```

escribir simplemente en código, usar:

```text
Runtime Registry
```

Cada runtime declara:

```yaml
runtime_type:
capabilities:
health_endpoint:
model_discovery:
deployment_type:
streaming:
tool_calling:
embeddings:
vision:
authentication:
```

Esto permite añadir nuevos runtimes sin modificar toda la UI.

---

# 46. Seguridad Wazuh

Wazuh debe integrarse como capa de seguridad real:

```text
Host Agent
Container monitoring
API audit
Filesystem integrity
Model artifact monitoring
Configuration monitoring
Authentication events
MCP security events
Tool execution events
Admin actions
```

Active Response únicamente mediante políticas explícitas:

```text
HIGH severity
+
rule_id
+
approved response
```

Ejemplos:

```text
revoke token
disable session
block source
quarantine artifact
disable model
```

Nunca ejecutar acciones destructivas desde una alerta sin una policy explícita.

---

# 47. Auditoría

Crear una auditoría central:

```text
audit_event
```

Campos:

```text
event_id
timestamp
actor
subject
action
resource
resource_id
source_ip
request_id
decision
reason
before_hash
after_hash
metadata
```

Todos los eventos críticos deberán poder reconstruirse.

---

# 48. WORM

No confundir:

```text
hash chaining
```

con:

```text
inmutabilidad absoluta.
```

El sistema debe implementar un ledger verificable:

```text
event_1
hash_1

event_2
hash(hash_1 + event_2)

event_3
hash(hash_2 + event_3)
```

y permitir:

```text
VERIFY CHAIN
```

pero además almacenar el ledger sobre un backend donde las modificaciones administrativas tengan controles adecuados.

---

# 49. Infraestructura reproducible

No utilizar:

```text
latest
```

para infraestructura importante.

Versionar:

```text
image tag
image digest
runtime version
config version
schema version
```

Separar:

```text
docker-compose.local.yml
docker-compose.dev.yml
docker-compose.prod.yml
```

o utilizar profiles correctamente, pero con archivos/configuración canónicos.

---

# 50. Eliminar las múltiples fuentes de verdad actuales

Hoy existen configuraciones repartidas entre:

```text
.env
docker-compose
SecretManager
Python
HTML
JS
Streamlit
```

Eso debe reducirse a:

```text
config/
    platform.yaml
    runtimes.yaml
    policies.yaml
    models.yaml
    tools.yaml
    agents.yaml
```

y secretos fuera de Git.

La base de datos registra el estado operativo.

Los YAML versionados contienen defaults declarativos.

La DB contiene runtime state.

Los artefactos viven en MinIO/S3.

---

# 51. Nueva estructura del repositorio

Propuesta:

```text
amp-cont-ai/
│
├── apps/
│   ├── control-plane/
│   └── research/
│
├── services/
│   ├── api/
│   ├── model-catalog/
│   ├── model-registry/
│   ├── inference/
│   ├── deployment/
│   ├── evaluation/
│   ├── data-platform/
│   ├── rag/
│   ├── mcp/
│   ├── agents/
│   ├── security/
│   └── observability/
│
├── packages/
│   ├── schemas/
│   ├── auth/
│   ├── policies/
│   ├── telemetry/
│   └── common/
│
├── plugins/
│   └── portops/
│       ├── datasets/
│       ├── features/
│       ├── models/
│       ├── tools/
│       ├── rag/
│       └── regulations/
│
├── configs/
│   ├── platform.yaml
│   ├── runtimes/
│   ├── models/
│   ├── policies/
│   ├── tools/
│   └── agents/
│
├── data/
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   └── quarantine/
│
├── artifacts/
│
├── infra/
│   ├── docker/
│   ├── compose/
│   ├── terraform/
│   └── kubernetes/
│
├── migrations/
│
├── scripts/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── e2e/
│   ├── security/
│   ├── data/
│   ├── mcp/
│   └── deployment/
│
├── docs/
│   ├── architecture/
│   ├── mlops/
│   ├── models/
│   ├── data/
│   ├── mcp/
│   ├── agents/
│   ├── security/
│   └── glossary/
│
├── .github/
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
│
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
└── README.md
```

---

# 52. APIs

Normalizar toda la API:

```text
/api/v1/auth
/api/v1/users
/api/v1/roles
/api/v1/policies

/api/v1/models
/api/v1/models/catalog
/api/v1/models/registry
/api/v1/models/{id}
/api/v1/models/{id}/versions

/api/v1/runtimes
/api/v1/runtimes/{id}/health
/api/v1/runtimes/{id}/models

/api/v1/deployments
/api/v1/deployments/{id}/verify

/api/v1/evaluations
/api/v1/experiments

/api/v1/datasets
/api/v1/datasets/{id}/lineage

/api/v1/mcp/servers
/api/v1/mcp/tools
/api/v1/mcp/access-requests

/api/v1/agents
/api/v1/souls

/api/v1/audit
/api/v1/telemetry

/api/v1/system/health
/api/v1/system/readiness
```

---

# 53. OpenAPI

El contrato OpenAPI debe generarse desde los mismos schemas que consume:

```text
frontend
Python SDK
CLI
tests
MCP adapters
```

Nunca mantener documentación manual separada del schema.

---

# 54. Schemas centrales

Usar Pydantic para:

```text
Model
ModelVersion
ModelRuntime
Deployment
Dataset
Experiment
Evaluation
User
Role
Policy
Tool
MCPServer
Soul
Agent
AuditEvent
```

Y generar JSON Schema automáticamente.

---

# 55. Tests obligatorios

### Unit

```text
catalog normalization
access policies
model resolution
artifact hashes
dataset validation
tool schemas
soul validation
```

### Integration

```text
API ↔ Registry
API ↔ MinIO
API ↔ vLLM
API ↔ PostgreSQL
API ↔ Redis
API ↔ MCP
API ↔ Wazuh
```

### Contract

```text
/v1/models
MCP initialize
MCP tools/list
MCP tools/call
OpenAPI
```

### E2E

```text
first-run
root creation
create user
assign model
deny model
enable model
deploy vLLM
verify runtime
run inference
request tool
approve tool
execute tool
audit event
```

---

# 56. Tests específicos para el problema actual

Debe existir una prueba que falle hoy y luego quede obligatoria:

```text
test_model_dropdown_matches_registry()
```

Debe comprobar:

```text
API catalog
==
UI catalog
```

Otra:

```text
test_no_hardcoded_models_in_frontend()
```

Otra:

```text
test_unhealthy_runtime_not_selectable()
```

Otra:

```text
test_unauthorized_user_cannot_infer()
```

Otra:

```text
test_tool_requires_approval()
```

Otra:

```text
test_vllm_model_matches_registry()
```

Otra:

```text
test_deployment_healthcheck_matches_api_routes()
```

---

# 57. Quality Gates

Antes de declarar una versión `release`:

```text
✓ lint
✓ type check
✓ unit tests
✓ integration tests
✓ contract tests
✓ E2E
✓ security scan
✓ dependency scan
✓ secret scan
✓ container scan
✓ model artifact verification
✓ data quality
✓ documentation build
```

---

# 58. CI/CD

Pipeline:

```text
commit
 ↓
lint
 ↓
type-check
 ↓
unit tests
 ↓
security scanning
 ↓
build
 ↓
integration tests
 ↓
container test
 ↓
model/runtime contract tests
 ↓
E2E
 ↓
artifact signing
 ↓
release
```

---

# 59. Supply Chain

Añadir:

```text
SBOM
dependency lock
container digest
artifact checksum
signature
provenance
```

Idealmente:

```text
SBOM
+
SLSA-style provenance
+
artifact signature
```

para releases.

---

# 60. MLOps lineage

Para cada inferencia poder reconstruir:

```text
User
 ↓
Prompt/Input
 ↓
Model
 ↓
Model Version
 ↓
Runtime
 ↓
Deployment
 ↓
Tools
 ↓
RAG
 ↓
Datasets
 ↓
Output
```

Eso convierte la plataforma realmente en un sistema auditable.

---

# 61. RAG

Separar:

```text
Document Store
Chunk Store
Embedding Store
Vector Index
Metadata Store
Retriever
Reranker
Citation Engine
```

Cada documento debe conservar:

```text
source_uri
source_hash
publication_date
effective_date
retrieved_at
document_version
section
page
authority
jurisdiction
```

Esto es especialmente importante para:

```text
HS Codes
ANA
MIDA
MINSA
APA
ACP
AMP
Leyes
Reglamentos
formularios
```

---

# 62. RAG arancelario

Debe existir jerarquía:

```text
HS 6 digits
        ↓
National Tariff
        ↓
Panama subheading
        ↓
Regulatory entity
        ↓
Permit
        ↓
Procedure
        ↓
Legal source
        ↓
Effective date
```

Nunca retornar únicamente:

```text
080390 = ...
```

Debe poder responder:

```text
Código
Descripción
Fuente
Fecha de vigencia
Entidad
Permiso
Base jurídica
Confianza
```

---

# 63. Marco legal

El módulo legal debe hablar de:

```text
SOURCE VERIFIED
```

y no:

```text
COMPLIANT
```

automáticamente.

La plataforma debe diferenciar:

```text
Legal source
Internal interpretation
Technical control
Compliance mapping
Certification
```

Solo debe afirmarse una certificación cuando exista evidencia independiente apropiada.

---

# 64. PortOps Pack

Migrar las capacidades actuales de AMP a:

```text
plugins/portops/
```

Incluyendo:

```text
port forecasts
AMP datasets
HS Code
ISO 6346
EDIFACT
Panama regulations
Maritime RAG
Monte Carlo
PortOps agents
PortOps Souls
```

Así el framework puede instalarse sin PortOps.

---

# 65. Modelo local entrenado desde cero

El framework debe permitir:

```text
Create Project
↓
Register Dataset
↓
Define Task
↓
Create Training Config
↓
Run Training
↓
Evaluate
↓
Register Artifact
↓
Create Version
↓
Approve
↓
Deploy
```

El modelo no necesita estar en Hugging Face.

Puede ser:

```text
models/my-model/
```

o:

```text
MinIO://models/my-model/version/
```

---

# 66. Fine-Tuning

Añadir perfiles:

```text
full_training
fine_tuning
lora
qlora
distillation
quantization
evaluation_only
```

Cada run debe registrar:

```text
base_model
dataset
training config
hardware
GPU
CUDA
framework version
seed
duration
loss
checkpoint
artifact
```

---

# 67. Hardware compatibility engine

El repositorio ya posee profiler de hardware, pero debe dejar de ser solamente una tarjeta visual.

Debe alimentar decisiones:

```text
GPU
VRAM
CUDA
CPU
RAM
disk
architecture
quantization
```

y determinar:

```text
compatible
compatible_with_warnings
not_compatible
```

Ejemplo:

```text
Model: 32B FP16
VRAM required: 65 GB
Host: 24 GB

Result:
NOT COMPATIBLE

Recommendations:
4-bit quantization
tensor parallel
CPU offload
smaller model
```

---

# 68. Deployment Profiles

Crear:

```text
local_cpu
local_single_gpu
local_multi_gpu
docker_gpu
kubernetes_gpu
edge_cpu
research
production
```

Cada uno tiene políticas propias.

---

# 69. Docker

Separar:

```text
control-plane image
api image
worker image
runtime image
vllm image
mcp image
```

No copiar modelos dentro de la imagen del API.

No copiar:

```text
mlflow.db
```

como mecanismo principal de registry.

Los modelos deben entrar por:

```text
volume
MinIO/S3
registry
artifact URI
```

---

# 70. Docker Compose

Debe tener solamente configuración declarativa.

Ejemplo conceptual:

```yaml
services:
  control-plane:
    ...

  api:
    ...

  postgres:
    ...

  redis:
    ...

  minio:
    ...

  model-registry:
    ...

  vllm:
    ...

  mcp:
    ...

  wazuh:
    ...
```

El modelo concreto debe declararse desde el deployment manifest.

---

# 71. Observabilidad

Instrumentar:

```text
OpenTelemetry
Prometheus
Grafana
structured logs
trace IDs
request IDs
model IDs
deployment IDs
```

Métricas:

```text
request count
error rate
latency
TTFT
tokens/sec
GPU utilization
VRAM
queue time
batch size
tool latency
RAG latency
retrieval count
```

---

# 72. Dashboard

No mostrar:

```text
Sistema 100% operativo
```

sin medirlo.

Mostrar:

```text
API HEALTHY
vLLM HEALTHY
PostgreSQL HEALTHY
MinIO HEALTHY
MCP 4/4 HEALTHY
Wazuh CONNECTED
```

El indicador global se calcula.

---

# 73. Estado del sistema

Utilizar:

```text
HEALTHY
DEGRADED
UNAVAILABLE
UNKNOWN
```

No utilizar únicamente:

```text
100% Operativo
```

---

# 74. Administración del modelo desde la UI

La pantalla del modelo debe tener:

```text
Overview
Versions
Artifacts
Evaluation
Deployment
Runtime
Access
Tools
Agents
Data Lineage
Audit
```

Un administrador debe poder:

```text
Register
Validate
Approve
Deploy
Stop
Restart
Promote
Rollback
Restrict
Publish
Archive
```

---

# 75. Rollback

Cada deployment debe conservar:

```text
previous_version
current_version
deployment_manifest
```

Permitir:

```text
Rollback
```

solo si:

```text
artifact exists
runtime compatible
approval policy satisfied
```

---

# 76. Modelo público vs modelo administrativo

Separar completamente:

```text
Model Discovery
```

de:

```text
Model Administration
```

y:

```text
Model Inference
```

Un usuario puede descubrir:

```text
Gemma
```

sin necesariamente poder:

```text
deploy Gemma
```

o:

```text
access Gemma
```

---

# 77. Playground público

El modo público puede existir pero con reglas:

```text
PUBLIC model
anonymous inference
rate limit
small context
limited tools
no sensitive RAG
no admin actions
no private datasets
```

---

# 78. Playground autenticado

Usuarios registrados pueden obtener:

```text
larger limits
history
saved prompts
model comparison
tool usage
RAG
exports
```

---

# 79. Playground verified

Usuarios verificados pueden obtener:

```text
advanced models
agent interactions
MCP tools
larger quotas
experiments
```

dependiendo de políticas.

---

# 80. Admin Playground

Solo administradores autorizados:

```text
raw runtime diagnostics
model configuration
deployment controls
tool testing
MCP testing
security testing
```

---

# 81. Acción seleccionable

Antes de ejecutar una operación, la UI debe preguntar:

```text
¿Qué deseas hacer?

[ Inferir ]
[ Comparar modelos ]
[ Evaluar modelo ]
[ Desplegar ]
[ Consultar RAG ]
[ Ejecutar tool ]
[ Ejecutar agente ]
[ Solicitar acceso ]
[ Auditar ]
```

Eso elimina la actual mezcla de funcionalidades en una sola pantalla.

---

# 82. Seguridad de tools

Categorías:

```text
READ
ANALYZE
WRITE
MODIFY
EXECUTE
DEPLOY
DESTRUCTIVE
```

Policies:

```text
READ → auto
ANALYZE → auto
WRITE → conditional
MODIFY → approval
DEPLOY → approval
DESTRUCTIVE → dual approval
```

---

# 83. Administración MCP

Nueva pantalla:

```text
MCP Servers

+ Add Server

Server
Transport
Version
Auth
Status

Tools
Resources
Prompts

Test
Permissions
Audit
```

Debe existir:

```text
Test Server
Test Tool
Test Authentication
Test Schema
Test Permission
```

---

# 84. Documentación para desarrolladores

README principal debe responder:

```text
What is it?
What problem solves?
Architecture?
How to install?
How to run?
How to add model?
How to add runtime?
How to add dataset?
How to add tool?
How to add MCP?
How to create agent?
How to contribute?
How to run tests?
How to deploy?
```

---

# 85. Documentación para usuarios

Separar:

```text
docs/user/
docs/admin/
docs/developer/
docs/mlops/
docs/security/
```

No mezclar todos los niveles en el README.

---

# 86. Filosofía Open Source

El framework debe poder ejecutarse:

```text
offline
local-only
Docker
Docker GPU
Kubernetes
single node
multi-node
```

Sin depender obligatoriamente de:

```text
OpenAI
Anthropic
Google
Microsoft
AWS
Azure
```

Los proveedores externos deben ser plugins/adapters.

---

# 87. Licencia

Revisar la licencia actual y especialmente cualquier “mandatory attribution” agregada sobre GPL.

La documentación debe distinguir:

```text
GPL obligations
project-specific notices
copyright notices
citation request
```

No presentar como una restricción estándar de GPL algo que realmente sea una cláusula adicional específica del proyecto.

---

# 88. Roadmap de implementación

## Fase 0 — Audit & Freeze

Congelar el estado actual.

Crear:

```text
ARCHITECTURE_BASELINE.md
KNOWN_LIMITATIONS.md
SOURCE_OF_TRUTH.md
```

Identificar:

```text
hard-coded models
hard-coded metrics
mock-like values
duplicate configs
duplicate routes
dead endpoints
security weaknesses
```

---

## Fase 1 — Core Platform

Implementar:

```text
database schema
configuration system
API versioning
RBAC/ABAC
audit
health/readiness
```

Eliminar configuraciones duplicadas.

---

## Fase 2 — Model Catalog

Implementar:

```text
Model Catalog API
VLLM Provider
HuggingFace Provider
Local Provider
Registry Provider
```

Después eliminar dropdowns hard-coded.

Este debe ser el primer cambio funcional visible.

---

## Fase 3 — Model Registry

Implementar:

```text
versions
artifacts
lineage
evaluations
approval
aliases
```

Migrar los ocho modelos actuales.

---

## Fase 4 — Real vLLM

Implementar:

```text
runtime manager
deployment manifests
runtime discovery
/v1/models discovery
health checks
smoke tests
tool-calling validation
GPU verification
```

La configuración vLLM actual con `google/gemma-2-9b-it` y versión fija antigua debe convertirse en un deployment profile versionado, no en una verdad global del sistema.

---

## Fase 5 — Frontend

Migrar a:

```text
React + TypeScript
```

Implementar:

```text
Model Catalog
Model Registry
User Management
Access Matrix
Runtime Dashboard
Deployment Wizard
```

---

## Fase 6 — MCP & Agentic

Implementar:

```text
MCP Registry
Tool Registry
Tool Policy
Access Requests
Agents
Souls
Execution Audit
```

---

## Fase 7 — Data Platform

Implementar:

```text
Data Catalog
Lineage
Quality Gates
Privacy
Provenance
Exports
```

Después migrar:

```text
AMP
HS Code
ANA
MIDA
MINSA
APA
ACP
```

como plugin PortOps.

---

## Fase 8 — Wazuh & Security

Implementar:

```text
identity events
model events
tool events
runtime events
file integrity
active response policies
security dashboard
```

---

## Fase 9 — Education

Implementar:

```text
Glossary
ML theory
formula engine
examples
interactive datasets
practical labs
```

---

## Fase 10 — Production Validation

Ejecutar:

```text
full installation
first-run
root creation
user creation
model discovery
model import
model deployment
vLLM health
inference
tool calling
MCP
RAG
security
audit
rollback
export
backup
restore
```

---

# 89. Criterio de aceptación final

La transformación se considera correcta únicamente cuando un usuario puede hacer esto sin editar código:

```text
1. Instalar framework
2. Ejecutar bootstrap
3. Crear Root
4. Configurar MFA
5. Configurar almacenamiento
6. Detectar GPU
7. Configurar vLLM
8. Descubrir modelos reales
9. Ver modelos disponibles
10. Filtrar modelos
11. Ver compatibilidad
12. Importar modelo
13. Registrar versión
14. Evaluarlo
15. Aprobarlo
16. Desplegarlo
17. Verificar runtime
18. Asignar acceso
19. Crear usuario
20. Asignarle modelo
21. Abrir Playground
22. Ejecutar inferencia
23. Invocar tool
24. Solicitar aprobación
25. Ejecutar MCP
26. Registrar auditoría
27. Ver telemetría
28. Exportar resultado
29. Revocar acceso
30. Rollback del modelo
```

Sin modificar HTML.

Sin editar Python.

Sin cambiar manualmente un dropdown.

Sin declarar a mano que un modelo existe.

Sin colocar métricas ficticias.

Sin ejecutar tools saltándose autorización.

---

# 90. Resultado arquitectónico deseado

El repositorio debe poder responder correctamente:

```text
¿Qué modelos existen?
```

```text
¿Qué modelos están disponibles actualmente?
```

```text
¿Qué modelos están realmente desplegados?
```

```text
¿Qué runtime los sirve?
```

```text
¿El runtime está saludable?
```

```text
¿Quién puede utilizar el modelo?
```

```text
¿Quién puede desplegarlo?
```

```text
¿Qué tools puede usar?
```

```text
¿Necesita aprobación?
```

```text
¿De qué dataset proviene?
```

```text
¿Qué versión del código lo produjo?
```

```text
¿Qué evaluación aprobó?
```

```text
¿Qué usuario ejecutó la inferencia?
```

```text
¿Con qué runtime?
```

```text
¿Qué tools utilizó?
```

```text
¿De dónde salió la información del RAG?
```

```text
¿Puede reproducirse?
```

```text
¿Puede auditarse?
```

Ese es el salto que necesita `amp-cont-ai`: pasar de **“aplicación que presenta capacidades MLOps”** a **“plataforma que realmente administra y verifica el ciclo de vida MLOps”**.

## Prioridad técnica inmediata

El primer bloque de implementación debería ser:

```text
1. SOURCE OF TRUTH
2. Configuration Registry
3. Model Catalog API
4. Runtime Registry
5. vLLM Discovery
6. Model Access Policy
7. User/Role Management
8. Real Deployment Verification
9. Frontend Model Catalog
10. Eliminar hard-coded model options
```

Después de eso deben construirse MCP, Agents, Souls, RAG y Wazuh sobre esas mismas primitivas, en vez de seguir agregándolos como módulos independientes.

La documentación actual de Hugging Face ya proporciona los mecanismos necesarios para búsqueda y filtrado de modelos, mientras vLLM proporciona mecanismos de serving y tool calling que permiten construir este catálogo de forma real y no simulada.

</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-09-26T19:46:48-05:00.

The user has mentioned some items in the form @[ITEM]. Here is extra information about the items that were mentioned by the user, in the order that they appear:

/goal is a [Slash Command]:
The user has marked this task with /goal, indicating that this task is intended to run for a long time without user input, e.g. overnight. You should be extra thorough and only stop when you are confident the goal has been completely fulfilled. The system will force you to continue execution, prompting you to audit your work until completion. Once complete, include <!-- GOAL_COMPLETE --> in your response. If the user explicitly asked to stop or cancel this goal, include <!-- GOAL_CANCELLED --> in your response to cancel the goal.
</ADDITIONAL_METADATA>