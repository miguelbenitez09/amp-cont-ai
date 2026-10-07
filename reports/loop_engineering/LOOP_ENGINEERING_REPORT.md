# Loop Engineering — ciclo de auditoría 2026-09-30

## Evidencia ejecutada

| Brecha | Cambio | Verificación | Estado |
|---|---|---|---|
| Wazuh no tenía contrato de administración de agentes | `WazuhClient` ahora expone capacidades y operaciones acotadas para listar, consultar, enrolar, retirar y rotar agentes. Las operaciones fallan explícitamente si el servicio no está configurado. | `tests/test_wazuh_client.py`: 3 passed; `capabilities()` devuelve `DISABLED_COMPATIBLE` sin credenciales. | Cerrada como compatibilidad; conexión viva pendiente de credenciales reales |
| Probe/catalogo apuntaban a vLLM en 8001 | Defaults normalizados a `http://127.0.0.1:8080/{health,v1}`. | `tests/test_unhealthy_runtime_not_selectable.py` y probe deben ejecutarse en el ciclo completo. | Cerrada como defecto de configuración |
| vLLM no sirve un modelo verificable | No se fabricó evidencia: el endpoint local no anuncia modelos. | `scripts/audit_gap_queue.py` sigue registrando `RUNTIME-VLLM-NO-MODEL`. | Abierta, requiere despliegue y prueba viva |
| Volúmenes de pesos Docker ausentes | No se fabricó un inventario falso; se registró el peso real gestionado por Ollama con digest en `data/metadata/model_inventory.json`. | `ollama list`, manifiesto local, digest SHA-256 y generación viva `OK` verificados. | Cerrada para Ollama; Docker/vLLM sigue pendiente |
| Catálogo local confundía candidatos con modelos instalados y usaba un fallback de GPU no verificado | `ModelDirectoryScanner` separa `candidate_catalog` de `models`, elimina Gemma4 no observado y usa la clave real `device_name` del profiler. | Escaneo local: `champion_models.joblib` y `qwen3:1.7b`; NVIDIA GeForce RTX 3050 Laptop GPU, 4 GiB, driver 546.30; `tests/test_model_scanner_truthfulness.py` pasa. | Cerrada |

| Ollama no estaba representado por el escáner de extensiones | El escáner ahora lee manifiestos content-addressed sin inferir modelos por nombre. | `qwen3:1.7b` detectado; `/api/generate` respondió `OK` con `think=false`, temperatura 0 y 2 tokens. | Cerrada |

| vLLM no tenía una ruta reproducible de despliegue | Se añadió `infra/vllm/docker-compose.vllm.yml` como perfil opt-in, con API key obligatoria, bind sólo a loopback, GPU NVIDIA, healthcheck y prefix/chunked caching. | `tests/test_vllm_deployment_contract.py` valida el contrato; no se declara servicio vivo porque Docker/vLLM no están presentes en este host. | Parcial: contrato cerrado, runtime vivo pendiente |

| El probe de vLLM no verificaba streaming | `VllmDeploymentProbe` ahora envía `stream=true`, exige `text/event-stream`, lee eventos SSE y registra el número de chunks. | `tests/test_unhealthy_runtime_not_selectable.py`: 2 passed; el endpoint ausente sigue reportándose como no verificado. | Cerrada en el código; evidencia viva pendiente |

| Los streams OpenAI-compatible pueden mezclar razonamiento interno con Markdown visible | `UnifiedLLMClient.parse_openai_sse` conserva sólo `delta.content`, ignora `delta.reasoning` y `[DONE]`. | `tests/test_llm_stream_parser.py` valida `Hola mundo` sin filtrar razonamiento. | Cerrada en el parser |

## Regla del siguiente ciclo

El inventario reproducible de modelos (Ollama/Hugging Face/Docker), digest y hardware ya está registrado. El siguiente ciclo debe ejecutar vLLM con un modelo compatible y verificar `/health`, `/v1/models`, completación y streaming antes de seleccionarlo. Las opciones de paged KV cache, prefix caching, continuous batching y speculative decoding permanecen sujetas a capacidades observadas del runtime.

La auditoría de cola posterior a este ciclo registra **1 brecha abierta**: runtime vLLM sin modelo servido. La ausencia de volumen Docker dejó de contarse como brecha porque el inventario Ollama está registrado y verificado; Wazuh queda en modo compatible-desactivado.

La política de Wazuh fue corregida: `WAZUH_ENABLED=false` es un estado compatible y verificable, no una falla. Si el operador activa Wazuh sin completar las tres variables de conexión, la cola vuelve a abrir la brecha de seguridad.

En este ciclo Docker Desktop fue verificado (`28.5.1`, runtime NVIDIA disponible) y `docker compose config` validó el contrato con una clave efímera de prueba. La descarga de `vllm/vllm-openai:v0.10.2` comenzó pero quedó incompleta/interrumpida antes de crear la imagen; por tanto el servicio vivo sigue sin evidencia y la brecha permanece abierta.

La cola ahora conserva esa evidencia en el finding de runtime: `docker_server=28.5.1`, `vllm_images=[]` y `model_count=0`. El campo `nvidia_runtime` de la auditoría CLI no se usa para declarar compatibilidad; el probe directo de `docker info` es la fuente autorizada.

La imagen `v0.10.2` finalmente quedó registrada localmente (34.2 GB), pero el arranque falló de forma reproducible: `nvidia-container-cli` exige CUDA >=12.8 y el driver anfitrión expone CUDA 12.3. Se retiró el contenedor fallido. La solución seleccionada es usar una imagen vLLM compilada para CUDA <=12.3 o actualizar el driver; no se fuerza una ejecución incompatible.

Se intentó `vllm/vllm-openai:v0.5.4` como alternativa CUDA-12.3. Docker descargó una capa, pero no completó el manifiesto ni registró la imagen; no se pudo iniciar. La evidencia confirma que la ruta requiere actualización del driver o una imagen compatible disponible en el registro.

La política de selección quedó explicitada en `configs/runtimes.yaml`: los cálculos numéricos usan `local_tabular`, las consultas de texto prefieren Ollama y vLLM sólo puede seleccionarse después de health/model/completion/streaming vivos. Mientras no se cumpla la matriz CUDA, Ollama es el fallback operativo verificable.

La ruta CPU de vLLM cerró la brecha de servicio: imagen `vllm/vllm-openai-cpu:latest`, modelo `Qwen/Qwen2.5-0.5B-Instruct`, `/health=200`, `/v1/models` con modelo, completación real y streaming SSE. El probe autenticado reportó **SERVING, 10/15**, con los checks 7–11, 13 y 14 aprobados. Los cinco checks restantes (GPU/CUDA, pesos fuera del contenedor, digest externo, tool calling y métricas) no se declaran aprobados en CPU.

Última auditoría: **1 brecha abierta**, imagen `v0.10.2` presente pero sin contenedor vLLM activo. El cierre requiere actualizar el driver CUDA del host o disponer de una imagen compilada para CUDA 12.3; no queda una corrección de código interna que pueda resolver esa incompatibilidad.

Se normalizó también la procedencia del modelo Ollama: el inventario distingue ahora `manifest_digest` de `weight_digest`, evitando confundir el identificador corto mostrado por `ollama list` con el hash del blob de pesos.

El camino matemático local permanece operativo mientras vLLM está bloqueado: `OptimizedInferenceEngine.predict_terminal` produjo bandas P10/P50/P90 para Balboa (155,877.3 / 195,244.9 / 219,952.2 TEUs), Cristóbal (81,138.7 / 94,224.2 / 126,990.7) y MIT (159,916.8 / 238,898.9 / 247,882.9). La garantía de orden P10 ≤ P50 ≤ P90 se mantiene en la ejecución.

## Limitaciones honestas

Wazuh permanece en modo compatible-desactivado porque no hay credenciales ni manager verificable en este entorno. La interfaz puede administrar el contrato, pero no afirma que exista conectividad. vLLM permanece sin modelo servido hasta disponer de pesos locales y una prueba reproducible.

## Regresión acumulada

El conjunto completo ejecutado después de los cambios acumulados: **208 passed, 1 skipped, 26 warnings**. Las advertencias provienen de nombres de features de scikit-learn y deprecaciones de `joblib`; no son fallos de ejecución.
