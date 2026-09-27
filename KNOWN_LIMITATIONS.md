# Known Limitations — amp-cont-ai (v1.0.0)

This document establishes the official catalog of architectural debts, legacy remnants, and known limitations being addressed under the MLOps Modernization Plan.

---

## 1. Hardcoded Model Dropdowns in Web UI
- **Location:** `src/serving/static/index.html` (lines ~200-240, `#algo-select`, `#sim-algo-select`) and `src/serving/static/js/app.js`.
- **Defect:** Options like "LightGBM Quantile Regressor", "XGBoost", "Random Forest" were hardcoded directly as HTML `<option>` tags instead of querying `GET /api/v1/models/catalog`.
- **Target Fix:** Dynamic population of all model selectors from the Model Catalog Service with runtime status badges (`HEALTHY`, `NOT LOADED`, `DEGRADED`).

## 2. Model Catalog & Registry Conflation
- **Defect:** Previously, "available models" in inference was conflated with "registered models in repository" or "benchmark models in offline tournament".
- **Target Fix:** Strict five-way separation:
  1. `Model Registry` (registered artifacts and versions)
  2. `Runtime Model Catalog` (physically reachable models)
  3. `Benchmark Catalog` (tournament metrics)
  4. `Model Access Catalog` (ABAC permissions)
  5. `Model Deployment Catalog` (active serving instances)

## 3. Synthetic Data Tagging
- **Location:** `src/data/connectors/external_sources.py` (L51-184), `src/data/lakehouse/panama_national_lakehouse.py`.
- **Defect:** Synthetic data generated via statistical distributions (`np.random.normal`, `np.sin`) was previously presented with official labels attributing it to ACP, AIS Spire, or Baltic Exchange.
- **Target Fix:** Explicitly tag all generated demo datasets with `⚠️ SYNTHETIC_DATA / DEMO ONLY` and require `USE_REAL_DATA=true` for production connectors.

## 4. Disconnected vLLM Probing
- **Defect:** The system previously checked whether Docker was installed or a config key existed, assuming vLLM was serving `DEFAULT_VLLM_MODEL`.
- **Target Fix:** Automated `vllm_probe.py` and `openai_compatible_probe.py` implementing the 15-point deployment verification checklist. If `/v1/models` does not return the model or returns an error, the model must be marked `CONFIGURED (NOT LOADED)` or `UNREACHABLE`.

## 5. Scattered Configuration Sources
- **Defect:** Configurations were distributed across `.env`, `SecretManager`, Python modules, and JavaScript files.
- **Target Fix:** Centralize all platform declarations into `configs/` (`platform.yaml`, `runtimes.yaml`, `models.yaml`, `policies.yaml`, `tools.yaml`, `agents.yaml`), with runtime state stored in SQLite database.

## 6. Monolithic Domain Coupling
- **Defect:** Port and customs analytics (TEU forecasting, HS Code tariff calculations, container ISO 6346) were intertwined with general MLOps platform abstractions.
- **Target Fix:** Decouple PortOps into `plugins/portops/`, keeping core MLOps platform abstractions domain-agnostic.
