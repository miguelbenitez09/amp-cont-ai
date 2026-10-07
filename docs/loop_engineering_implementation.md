# Implementación del ciclo de ingeniería

## Estado ejecutado

- **Inventario local:** Docker no contiene imágenes, contenedores ni volúmenes. No se localizaron pesos Gemma 2/Gemma 4. Ollama contiene `qwen3:1.7b` Q4_K_M, con digest registrado en `configs/model_candidates.yaml`.
- **Inferencia de texto:** el selector valida modelos mediante los endpoints de catálogo. Ollama quedó operativo en CPU porque el controlador NVIDIA 546.30 no ejecuta los kernels CUDA del runtime instalado. vLLM usa el puerto dedicado 8080 y permanece deshabilitado hasta superar pruebas vivas.
- **Predicción matemática:** el Feature Store registra hashes de sus fuentes Silver y prohíbe filas sintéticas. Las categorías ausentes del pivot se codifican como cero de dominio; lags, rolling y crecimientos desconocidos se imputan únicamente con datos de cada ventana de entrenamiento. El benchmark compara LightGBM cuantílico, Random Forest, Gradient Boosting y Ridge.
- **Gobernanza:** la promoción exige `p50_wape` finito. La cola `data/gold/governance/gap_queue.json` deduplica hallazgos, conserva asignación/historial y reabre regresiones.
- **Fuentes externas:** los conectores aceptan únicamente CSV acompañados por manifiesto `OBSERVED`, URL, fecha y SHA-256. Las simulaciones nacionales requieren opt-in y no entran al flujo productivo.
- **Interfaz:** la salida Markdown se procesa con un renderizador local que escapa HTML antes de aplicar un subconjunto controlado de Markdown.
- **Seguridad:** Wazuh dispone de adaptador JWT y estado explícito `UNCONFIGURED` hasta que existan secretos reales.

## Ciclo automático de brechas

1. `python scripts/audit_gap_queue.py` ejecuta reglas deterministas sobre runtimes, inventario de modelos, procedencia y seguridad.
2. Cada regla produce un fingerprint estable, severidad, evidencia, rol propietario y remediación.
3. `GapQueue.upsert` incrementa ocurrencias, conserva asignaciones, resuelve reglas que dejan de reproducirse y reabre regresiones.
4. `GET /api/v1/governance/gaps` publica la cola para la interfaz y auditoría.
5. La validación debe ejecutar pruebas, un smoke test HTTP y el benchmark temporal antes de cerrar una brecha.

## Brechas abiertas verificadas

- vLLM no está desplegado y Docker no expone runtime NVIDIA; no se presenta como funcional.
- Wazuh no tiene URL ni credenciales configuradas.
- Las fuentes observadas de ACP, AIS y fletes deben incorporarse con sus manifiestos antes de enriquecer modelos productivos.
- El modelo Qwen local necesita una evaluación RAG propia del dominio antes de recibir una etiqueta de calidad normativa.
