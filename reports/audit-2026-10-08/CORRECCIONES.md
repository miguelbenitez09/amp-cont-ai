# Correcciones verificadas — 8 de octubre de 2026

Las nueve brechas documentadas en la auditoría tienen correcciones implementadas. Los servicios locales de `http://127.0.0.1:8000/app` están ejecutando las versiones corregidas. Esto no certifica preparación completa para producción: permanecen las áreas no verificadas del informe original.

| Hallazgo | Corrección | Verificación |
|---|---|---|
| A01: administración sin sesión | Dependencias de sesión y rol en rutas antiguas de usuarios, revocación, configuración, infraestructura, presets y MCP. Bloqueo de cuentas inactivas y de operaciones administrativas antes de rotar una contraseña temporal. | Invitado→401; usuario de consulta→403; administrador→servicio autorizado. Registro de cuenta con rotación obligatoria en base temporal. |
| A02: inventario expuesto | Inventario administrativo e infraestructura requieren permiso administrativo. | Ambos GET devuelven 401 en el servidor real sin sesión. |
| A03: CORS permisivo | Denegación por defecto, comparación exacta de orígenes y eliminación del CORS permisivo del upstream. | Origin example.com→403 en preflight real; sin Allow-Origin. Pruebas de origen válido, cadenas malformadas y upstream permisivo. |
| A04: cabeceras ausentes | Go aplica CSP, Permissions-Policy, COOP, CORP y DENY a /app; evita duplicar la política del backend. | HTTP real y pruebas del gateway; cabeceras únicas y coherentes. |
| A05: indicadores ficticios | TLS y respaldos quedan como no verificados; las cookies muestran la configuración real. Errores del inventario se registran y producen estado degradado. | Pruebas de metadatos y fallo de SQLite. |
| A06: modal de acceso | Diálogo con nombre accesible, foco inicial, fondo inerte, recorrido de teclado contenido, Escape y devolución del foco. | Chromium en 390×844, 768×1024 y 1440×900, incluidos 18 pasos de Tab por tamaño. |
| A07: controles sin nombre | Nombres accesibles para los selectores de idioma y tema. | Comprobación DOM y prueba del navegador. |
| A08: smoke obsoleto | Selector de traducción vigente, más comprobaciones del modal y navegación. | Smoke completo aprobado en los tres tamaños. |
| A09: token persistido | Se elimina localStorage para el bearer y se limpia el valor de versiones anteriores. Recarga mediante cookie HttpOnly; /me no devuelve el bearer. Integridad SHA-384 y crossorigin en las dependencias CDN. | Pruebas del contrato, sesión real en base temporal y navegador: login→recarga→escritura→logout. |

También se añadió protección CSRF para solicitudes mutables con sesión por cookie. La interfaz incorpora el token de protección y lo actualiza al emitir o rotar sesión. Se rechazan orígenes ajenos y se auditan los rechazos. Un cierre de sesión fallido comunica el error y conserva el estado local hasta que el servidor confirme la revocación.

## Resultados

- **45 pruebas de Python aprobadas**: seguridad, cabeceras, interfaz, contratos JS y estados de UI; incluyen el E2E de sesión en Chromium con un servidor HTTP y una base temporal.
- **6 pruebas de compatibilidad aprobadas**: perfiles, configuración de infraestructura y metadatos de seguridad. Los tests de configuración usan almacenamiento temporal y contexto autorizado explícito.
- **Pruebas de Go aprobadas**, incluidas regresiones de CORS, política del HTML, cabeceras duplicadas y origen reenviado.
- **Smoke visual aprobado** en los tres tamaños; idiomas, validaciones, bloqueo aduanero y modal.
- Sintaxis de los tres archivos JS modificados y validación de traducciones aprobadas.

Archivos de evidencia: `regression-after.txt`, `compatibility-after.txt`, `gateway-tests-after.txt`, `http-after.json` y `smoke-after.json`.

## Uso y límites

Los clientes que usan cookies deben obtener `csrf_token` desde GET `/api/v1/auth/me` y enviarlo en `X-CSRF-Token` para las operaciones mutables. Los clientes Bearer siguen usando Authorization y no persisten credenciales en la interfaz. Orígenes CORS adicionales requieren configuración explícita mediante `PORTOPS_CORS_ORIGINS`; la protección de escritura del backend sigue exigiendo el origen propio.

La CSP conserva `unsafe-inline` para los manejadores y estilos existentes. Ya existe una política efectiva en /app, pero migrar esos manejadores a listeners y aplicar nonces/hashes es endurecimiento pendiente. Los scripts del CDN ahora tienen integridad, sin afirmar ausencia de vulnerabilidades en sus versiones.

No se instalaron Firefox ni WebKit y no se verificaron lectores de pantalla, WCAG completo, Core Web Vitals, aislamiento multi-tenant, todos los roles, MFA completo ni restauración real de respaldos. El E2E usa cuentas temporales, no credenciales de usuarios de la instalación activa. Las comprobaciones realizadas no equivalen a ejecutar toda la suite del proyecto.

Reproducir: `python -m pytest tests/test_audit_20261008_security.py tests/test_security_gateway.py tests/test_frontend_auth_and_hover_ui.py tests/test_js_package_guardrails.py tests/test_ui_state_machine.py -q`, `go test ./cmd/gateway` y `python scripts/ui_smoke_playwright.py --url http://127.0.0.1:8000/app`.
