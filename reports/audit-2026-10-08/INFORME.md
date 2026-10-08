# Auditoría de /app — 8 de octubre de 2026

Este documento conserva el resultado inicial. Las correcciones posteriores y su verificación están en [CORRECCIONES.md](CORRECCIONES.md).

**Dictamen: no declarar listo para producción.** La autorización administrativa presenta defectos bloqueantes. Se revisaron código, HTTP del servicio real y Chromium a 390×844, 768×1024 y 1440×900. Esta revisión no constituye certificación ni cobertura completa de ASVS o WCAG.

## Hallazgos confirmados

### A01 — Crítica: creación administrativa accesible sin sesión

`src/serving/api.py:2525` expone POST `/api/admin/users` sin dependencia de identidad o autorización. La prueba con FastAPI TestClient, sin cookies ni Authorization, obtuvo HTTP 200 y una llamada al servicio de registro. Se sustituyó `register_user` por un simulador: no se creó ninguna cuenta real. El servicio real acepta `platform_admin`, asigna ese rol en SQLite y no exige cambio inicial de contraseña. El impacto incluye creación de cuentas privilegiadas; la creación persistente y el inicio de sesión de esa cuenta no fueron ejecutados.

Otras rutas sin control en este archivo incluyen revocación de sesiones, eliminación de usuarios, escritura de configuración y políticas de guardrails. Su ausencia de control se confirmó por código; sus efectos destructivos no se ejecutaron.

Corrección: aplicar una dependencia central de sesión activa y permisos por operación a todas las rutas antiguas, incluyendo denegación por defecto. Verificar invitado→401, rol insuficiente→403 y administrador autorizado→resultado real. No basta ocultar las pestañas.

### A02 — Alta: exposición del inventario de usuarios y configuración

GET `/api/admin/governance` y `/api/v1/infra/config` devuelven HTTP 200 sin sesión en el servicio de puerto 8000. El inventario incluye usuarios, correos, roles, estado y marcadores de cuenta root; la configuración expone metadatos de infraestructura. No se copiaron identidades ni secretos al informe. La prueba de aceptación del inventario falla: devuelve 200 cuando debería requerir autorización.

Corrección: exigir permisos de lectura administrativa y separar información pública de inventarios privados. Evaluación asociada: WSTG, autorización y exposición de información.

### A03 — Alta: CORS refleja un origen externo con credenciales

En OPTIONS y GET `/api/admin/governance`, `Origin: https://example.com` obtuvo `Access-Control-Allow-Origin: https://example.com` y `Access-Control-Allow-Credentials: true`. También se reflejaron dos cadenas de origen no válidas con sufijo `evil.example`; estas últimas demuestran validación textual deficiente, no una explotación desde un origen válido de navegador.

El código actual de `cmd/gateway/main.go:231` utiliza prefijos para confiar en localhost, pero no explica por sí solo la aceptación de example.com: existe una discrepancia entre el comportamiento desplegado y el código revisado. No se verificó lectura desde una página externa con sesión; las restricciones del navegador, cookies y acceso a redes locales pueden limitarla.

Corrección: identificar el binario/proceso/configuración realmente activos y usar una lista exacta de orígenes normalizados; no reflejar orígenes arbitrarios. Emitir `Vary: Origin` cuando corresponda. ASVS V3 y WSTG CORS.

### A04 — Media: /app pierde los controles de seguridad del backend

GET `/app` carece de Content-Security-Policy, Permissions-Policy, COOP y CORP. El backend sí entrega esas cabeceras en las respuestas inspeccionadas; Go sirve el HTML directamente y solo añade un subconjunto. X-Frame-Options es SAMEORIGIN en /app y aparece duplicado como `SAMEORIGIN, DENY` en respuestas del backend. No se demostró XSS ni clickjacking explotable.

Corrección: aplicar una política coherente en el borde, sin cabeceras contradictorias; definir CSP compatible con las dependencias y reducir scripts inline mediante nonces o hashes. Añadir pruebas HTTP al gateway real: `tests/test_security_gateway.py` solo prueba FastAPI y no detecta esta ruta. ASVS 5.0.0 V3.

### A05 — Alta: el panel informa protección sin comprobarla

`src/infrastructure/security/governance_panel.py:193` devuelve valores fijos: TLS 1.3, certificado válido hasta 2027-12-31, SameSite Strict, cookie `AMP_SESSION_TOKEN_SECURE`, CSP estricta, RPO/RTO y backups aislados. La URL auditada utiliza HTTP; /app carece de CSP. La implementación de sesiones en `src/serving/v1_router.py:83` usa `portops_session`, SameSite Lax y Secure condicional. Las afirmaciones no constituyen mediciones. No se verificaron TLS de una instalación externa ni respaldos.

Corrección: derivar estados de comprobaciones reales y mostrar «no verificado» cuando falte evidencia; separar objetivos de recuperación de resultados de ejercicios medidos. Es bloqueante usar estos indicadores como aprobación de producción.

### A06 — Media: modal de acceso sin semántica ni traslado de foco

Al pulsar `#btn-auth-iam`, `#auth-iam-modal` no tiene role=dialog ni aria-modal; el foco permanece en el botón exterior en los tres tamaños. Escape sí cierra el modal. No se midió el ciclo completo de foco con lector de pantalla.

Corrección: nombre accesible del diálogo, role/aria-modal, foco inicial dentro del modal, fondo inerte, navegación contenida y retorno al disparador. Criterios relacionados: WCAG 2.2, 2.4.3 y 4.1.2; verificar además teclado 2.1.1.

### A07 — Media: selectores de idioma y tema sin nombre accesible explícito

`#nav-lang-select` y `#theme-selector` no tienen label asociado, aria-label, aria-labelledby ni title propio. El título está en el contenedor y no sustituye un nombre accesible del control. Confirmado por DOM y código en los tres tamaños; no se ejecutó axe-core ni un lector de pantalla.

Corrección: asociar etiquetas o nombres accesibles localizados y verificar el árbol de accesibilidad. WCAG 2.2, 4.1.2.

### A08 — Media: la prueba visual existente no puede completar su cobertura

`python scripts/ui_smoke_playwright.py --url http://127.0.0.1:8000/app` termina con TimeoutError al buscar `[data-i18n='landing.evidence_badge']`, que no está en la página actual. No produce el resultado final ni completa todos los tamaños. Las pruebas estáticas que buscan tokens CSS o clases de ocultamiento no prueban contraste ni autorización.

Corrección: actualizar el contrato de selectores y separar aserciones de contenido, accesibilidad y seguridad. Conservar fallas visibles, sin convertir errores de prueba en aprobaciones.

### A09 — Media: persistencia del token en almacenamiento legible por JavaScript

`src/serving/static/js/auth_flow.js:171` guarda el token de sesión en localStorage y lo recupera tras recargar. Esto se confirmó por código, sin iniciar sesión. Un script ejecutado en el origen podría leerlo; combinado con ausencia de CSP y scripts CDN sin integrity amplía el impacto de una ejecución de JavaScript comprometida. No se confirmó una vía XSS ni compromiso del CDN.

Corrección: preferir sesión por cookie HttpOnly y evitar devolver/persistir el bearer cuando no sea necesario; aplicar protección CSRF a operaciones autenticadas por cookie y verificar rotación, revocación y expiración.

## Comprobaciones que sí funcionaron

- /app y /health/ready responden HTTP 200.
- La calculadora rechaza HS/CIF vacíos y muestra recuperación: «Completa un código HS y un valor CIF mayor que cero».
- HS 2710.19.21.00.00 y CIF 10000 generan un bloqueo explicado por falta de evidencia documental; HTTP 422 es esperado en este flujo, no un fallo del sistema.
- La validación de contenedor vacío exige identificador ISO 6346 de 11 caracteres.
- Idiomas es/en/pt cambian el atributo lang en los tres tamaños; no se comprobó traducción completa.
- No hubo excepciones JavaScript en los flujos públicos ejercitados. Esta observación no cubre todos los eventos.

## Evidencia y reproducción

- `evidence.json`: cabeceras/status reales, observaciones DOM, calculadora, idiomas y layout.
- `initial-*.png` y `customs-viewport-*.png`: capturas en los tamaños evaluados. Las capturas initial se toman al final del flujo y muestran Aduanas; el nombre se conserva por compatibilidad con el recolector.
- `scripts/audit_live_20261008.py`: recolector repetible, sin escritura administrativa.
- `tests/test_audit_20261008_security.py`: dos pruebas de aceptación, **2 fallidas**, correspondientes a A01/A02. La creación está simulada; TestClient puede emitir registros de auditoría y ejecutar inicialización habitual.

Ejecutar desde la raíz: `python scripts/audit_live_20261008.py` y `python -m pytest tests/test_audit_20261008_security.py -q`. Las pruebas fallidas documentan defectos abiertos; no se aplicaron correcciones de producto.

## Límites y pendientes

El chequeo de overflow basado únicamente en documentElement devuelve falso, pero después del flujo Aduanas el body mide 1036 px con viewports de 390 y 768 px. También hay elementos con rectángulos fuera del viewport. Esto requiere distinguir elementos ocultos, carruseles y contenido recortado antes de atribuir un incumplimiento de reflow: **responsive completo no verificado**. No debe aprobarse con esa sola aserción.

No verificado: inicio de sesión real, MFA, rotación/revocación/expiración completas; matriz de roles; aislamiento multi-tenant e IDOR/BOLA con dos usuarios; CSRF y XSSI explotables; Firefox/WebKit; lectores de pantalla; axe-core; Lighthouse/Core Web Vitals, memoria, carga/concurrencia, recuperación de red, restauración de backups y SAST/DAST completos. No se asignan porcentajes de cobertura ni cumplimiento global. La revisión de código de rutas antiguas no demuestra que cada efecto interno funcione.

Prioridad: cerrar A01/A02 y verificar las demás rutas administrativas; resolver A03; sustituir los indicadores fijos A05; unificar cabeceras A04; completar pruebas por roles y accesibilidad. Mantener el bloqueo de producción hasta verificar las correcciones con regresiones.

Referencias oficiales: [OWASP ASVS 5.0.0](https://github.com/OWASP/ASVS/tree/v5.0.0/5.0), [OWASP WSTG v4.2](https://wstg.owasp.org/v4.2/), [WCAG 2.2](https://www.w3.org/TR/WCAG22/). Se usan como marco de clasificación, no como certificación.
