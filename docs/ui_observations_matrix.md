# Matriz de observaciones de interfaz (1–34)

La matriz vincula cada grupo de comentarios con una corrección verificable. Una
observación marcada como pendiente requiere una fuente o flujo que todavía no
está disponible; no se resuelve rellenando texto aparente.

| Comentarios | Área | Corrección aplicada | Evidencia | Estado |
|---|---|---|---|---|
| 1 | Shell y navegación | Barra de pestañas desplazable, foco visible y controles táctiles | `scripts/ui_smoke_playwright.py`, 390/768/1440 px | Verificado |
| 2 | Validación ISO | Entrada obligatoria, alfabeto ASCII ISO 6346, cálculo de dígito separado de manifiesto | `tests/test_ana_agreements_scraper.py`, endpoint `/containers/validate` | Verificado |
| 3–5 | Calculadora aduanera | HS y CIF explícitos; HTTP 422 y `N/D`; liquidación bloqueada sin evidencia documental ANA | `tests/test_agents_customs_mcp.py`, smoke Playwright, `evidence_status` | Verificado |
| 6–7 | Acciones Liquidar/CoT | Acciones visibles con datos de la tarjeta y sin liquidar históricos sin vigencia | `customs_rag.js`, búsqueda `/customs/tariff/search` | Verificado |
| 8–9, 22 | Código HS y detalle | Código, HS-6, periodo, clasificación histórica y procedencia separados; portal oficial ANA identificado | `build_tariff_catalog.py`, `compare_recovery_imports.py`, `ana_interactive_tariff_portal` | Parcial: 17 referencias ANA 404 y PDF arancelario no descargable en esta ejecución |
| 10–21 | Navegación, filtros e iconos | Controles coherentes, ocho filtros, estado `N/D` en campos no respaldados | Smoke Playwright: `quick_filter_count=8`, sin `undefined` | Verificado |
| 23 | Lakehouse | Bronze/Silver/Gold separados; Silver normaliza los 700 registros y conserva la barrera `publication_ready=false` | `scripts/build_ana_silver_catalog.py`, `data/silver/ana_agreements_catalog.manifest.json` | Parcial: falta publicación ANA completa |
| 24 | Inicio de sesión | Invitado no administra usuarios; sesión Bearer/cookie para operaciones protegidas | `tests/test_real_user_management.py`, runtime 401 | Verificado |
| 25 | Modelo y Settings | Acceso separado del estado de servicio; sin afirmar disponibilidad no medida | `app.js`, `/health`, smoke runtime | Verificado |
| 26 | Disponibilidad | Badge alimentado por `/health`, sin texto fijo “100% Operational” | `/health` devuelve `healthy` | Verificado |
| 27 | Latencia | Latencia se muestra solo cuando existe medición registrada | `/telemetry/summary`, KPI `N/D` sin registros | Verificado |
| 28–30 | Entidades AMP/MiAmbiente/Energía | Entidades provienen del catálogo y muestran enlace institucional con alcance explícito | `REGULATORY_ENTITY_SOURCES`, `customs_rag.js`, pruebas de procedencia | Parcial: la página institucional no prueba aplicabilidad legal por partida |
| 31–33 | Permisos y procedimientos | Permiso, importación, exportación y base legal sin textos de relleno | `customs_rag.js`, evidencia por documento/página | Parcial: extracción legal pendiente en referencias faltantes |
| 34 | Idiomas | ES/EN/PT materializados por rutas nativas y selector persistente | `scripts/validate_i18n.js`, smoke Playwright | Verificado |

## Criterio de cierre

Una fila pasa a “Verificado” solo cuando existe una prueba o manifiesto que
demuestra el comportamiento y la procedencia. Los 17 enlaces ANA que responden
404 permanecen en `data/gold/ana_agreements_recovery/source_register.json` con
tipo de acuerdo, URL, fecha de comprobación y alternativa oficial o estado de
no localización.

## Auditoría Manual Exhaustiva UI en Vivo (http://127.0.0.1:8000/)

- **Fecha de Auditoría:** 2026-10-05T19:03:00-05:00.
- **Herramienta de Auditoría:** Playwright Headless Chromium (`scripts/test_ui_deep_inspection.py`).
- **Errores No Controlados de Página (`Page Errors`):** 0.
- **Pestañas Navegadas (10/10):** Inicio & Visión General, Razonamiento CoT & Agentes, Aduana & RAG, Pronóstico & What-If, Comparativa Multi-Algoritmo, Diagnóstico Estadístico, Simulación Monte Carlo, Metodología, Data Platform & Calidad, Seguridad/IAM/WORM. Todas con estado **OK**.
- **Autenticación y Presets IAM:**
  - Preset Root Admin probado: Autenticación exitosa.
  - Rol activo HUD actualizado a: `Rol: root`.
  - Notificación de primer inicio: `Sesión verificada. Cambio obligatorio de contraseña requerido.`
- **Inferencia TEU y Modelos:**
  - Pronóstico TEU ejecutado: Inferencia P50 = `195,245 TEUs`.
  - Simulación Monte Carlo: VaR 95% = `195,245 TEUs`.
- **Gobernanza y Aduana:**
  - Validación de contenedor ISO 6346: Correctamente detecta contenedores válidos y reporta error de dígito verificador Mod-11 en códigos inválidos.
  - Calculadora de Liquidación: Validación de campos vacíos activa; liquidación bloqueada para reglas sin respaldo documental verificable (HTTP 422 - Anti-Tamper Regulatory Compliance).
- **Quality Gates 5D:** Evaluado en vivo con puntuación `1.00 / 1.00`.
- **i18n & Theming:** Verificados 3 idiomas (`es`, `en`, `pt`) y 6 esquemas visuales.
- **Evidencias Capturadas:** 19 capturas en `docs/assets/audit/manual_tests/` y reporte JSON en `logs/audit_runs/manual_deep_ui_audit.json`.

## Reestructuración Integral del Flujo de Autenticación, Centro IAM y Onboarding

- **Fecha de Validación:** 2026-10-05T19:33:00-05:00.
- **Script de Automatización E2E:** `scripts/test_ui_auth_workflow.py`.
- **Correcciones de Raíz Implementadas:**
  1. **Eliminación Total de Presets de Prueba 1-Clic:** Se retiró por completo la barra de botones rápidos (`Root Admin`, `Auditor`, `Operador`, `Aduanas`) en cumplimiento de los estándares NIST SP 800-63B e ISO/IEC 27001. El acceso requiere credenciales reales de sistema (`root` con clave inicial de `.bootstrap/root-credentials.txt`).
  2. **Corrección de Cierre de Modales ('X' y Botón Footer):**
     - Se unificó `closeAuthModal` y `closeFirstRunModal` para limpiar los estilos en línea (`style.display = 'none'`, `visibility = 'hidden'`, `opacity = 0`, `pointerEvents = 'none'`), eliminando el bloqueo que impedía cerrar el modal al hacer clic en la 'X' o en "Cerrar Centro IAM".
     - Se añadieron escuchadores para clic fuera del modal (backdrop) y para la tecla `Escape`.
  3. **Desanidamiento del DOM HTML:** Se resolvió un defecto crítico en `src/serving/static/index.html` donde `settings-modal` carecía de dos etiquetas de cierre `</div>`, causando que `auth-iam-modal` y `first-run-setup-modal` quedasen atrapados dentro de un contenedor con `display: none` (dimensiones 0x0).
  4. **Persistencia Activa del Token y Sesión:**
     - El endpoint `/api/v1/auth/password/change` ahora genera de inmediato un nuevo token de sesión firmado para el usuario tras revocar las credenciales viejas, actualiza la cookie de transporte y devuelve `session_token`.
     - El frontend actualiza `localStorage.setItem('portops_token', ...)` y el objeto `window.activeSession`.
     - Al recargar la página (`F5`), `restoreSessionState()` restaura la sesión activa conservando el rol `Rol: root` y el estado del usuario sin regresar a modo invitado ni emitir errores 401.
  5. **Flujo Guiado de Configuración Inicial (First-Run):**
     - La landing page y la demo operativa se despliegan limpias sin popups invasivos al cargar el sitio.
     - Al autenticarse como superadministrador con la contraseña temporal de instalación, el sistema detecta `must_change_password: true` y guía al usuario de manera fluida hacia el cambio obligatorio de contraseña (con comprobación de entropía y coincidencia).
     - Una vez confirmada la clave, se avanza a la provisión obligatoria de los tres administradores segregados (`SysAdmin`, `SecOpsAdmin`, `MlopsAdmin`), desbloqueando todas las capacidades operativas del Framework.
- **Evidencias Gráficas Registradas:** 7 capturas en `docs/assets/audit/manual_tests/auth_flow/`:
  - `01_landing_unblocked.png`: Landing y demo despejadas en carga inicial.
  - `02_iam_modal_no_presets.png`: Centro IAM sin botones de prueba rápida.
  - `03_modal_closed_by_x.png`: Cierre efectivo mediante el botón 'X'.
  - `04_mandatory_pwd_change_prompt.png`: Activación del cambio obligatorio de clave.
  - `05_pwd_changed_session_active.png`: Transición con sesión activa y token renovado.
  - `06_authenticated_hud_state.png`: HUD operativo reflejando `Rol: root` y `root (Salir)`.
  - `07_session_persisted_after_reload.png`: Preservación intacta de la sesión tras recargar la página.


