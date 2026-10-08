# Plan avanzado de implementación y QA integral

Fecha: 8 de octubre de 2026. Estado: **propuesto; pendiente de la palabra «Continuar»**.

Este documento se redacta a partir de lectura de código, revisión de evidencia anterior y análisis de tres agentes. No se ejecutó una nueva auditoría funcional completa, no se modificó la aplicación, no se cambiaron credenciales ni se reiniciaron servicios durante esta planificación. Guardar este plan es el único cambio previsto en esta etapa.

## 1. Objetivo y definición de terminado

Demostrar que cada operación publicada tiene una interfaz utilizable, contrato de API correcto, autorización en servidor, resultado real, persistencia cuando corresponde, auditoría y recuperación. Corregir los defectos confirmados con pruebas de regresión. Toda capacidad anunciada debe estar implementada o identificada explícitamente como no disponible; una maqueta, respuesta HTTP o catálogo no demuestran un flujo completo.

La aceptación se realizará por caso de uso y entorno. No se afirmará que «todo funciona» si hay operaciones inventariadas pendientes. Un servicio externo no configurado queda bloqueado por dependencia y no cuenta como aprobado. El plan no implica construir un equivalente completo de Fabric/Databricks: delimita las capacidades del producto y completa sus flujos publicados.

Marcos de referencia: [OWASP ASVS 5.0.0](https://github.com/OWASP/ASVS/releases/tag/v5.0.0), [OWASP WSTG v4.2](https://wstg.owasp.org/v4.2/) y [WCAG 2.2 AA](https://www.w3.org/TR/WCAG22/). En ejecución se registrarán requisitos concretos, versión, aplicabilidad y evidencia; no se atribuirá conformidad completa a una herramienta automática.

## 2. Línea base y límites conocidos

La ronda anterior registró 115 pruebas aprobadas, 12 cuentas locales, 96 comprobaciones de acceso y 64 pantallas de gestión recorridas en Chromium. Es evidencia histórica, no una verificación completa actual ni prueba de todas las operaciones de negocio. Parte de la matriz de escritura sólo comprueba permiso de ruta mediante rechazo 422 a cuerpos vacíos.

Superficies identificadas:

| Superficie | Interfaz | Contratos observados | Riesgo a resolver |
|---|---|---|---|
| Operación portuaria | `/app` | `/api/v1/auth`, rutas operativas, simulación y MCP | Controles legacy, identidad de ejecución, errores y respuestas fuera de orden |
| Gestión de instancia | `/static/workspace/` | `/api/workspace`, identidad `/api/v1/auth` | Confirmaciones, persistencia, delegación y operaciones completas |
| Framework | `/static/framework/app.html` y aplicación de `src/framework/app.py` | `/api/auth`, `/api/datasets`, `/api/training`, `/api/models` | Determinar qué servidor lo publica; evitar sesiones, permisos o botones incompatibles |
| Gateway e infraestructura | Go puerto 8000 → API puerto 8001 en la instancia anterior | Proxy, estáticos y políticas de origen | Verificar configuración real, upstream, rutas y comportamiento tras reinicios |

Indicios de lectura que requieren reproducción antes de clasificarse como defectos confirmados:

- Frontend operativo conserva llamadas de administración/secretos retiradas con 410.
- Framework contiene vistas de datasets/entrenamiento con catálogo o instrucciones, y agentes MCP «No disponible».
- Existe una llamada de predicción con host absoluto local; probar otro host, HTTPS y prefijos.
- Se encontraron seis temas operativos/de gestión y cinco del framework; no asumir cobertura uniforme.
- Borradores y aviso de cambios sin guardar no cubren todos los formularios.
- Permisos de rutas legacy se resuelven con lista explícita y retorno sin capacidad para rutas no enumeradas: requiere inventario completo y decisión de política por ruta.
- Confirmación y escritura, así como validación de privilegios y escritura, requieren pruebas de atomicidad y carreras concurrentes.
- Las excepciones de MFA para cuentas manuales necesitan delimitación por entorno y caducidad; las migraciones deben impedir autorización abierta ante tablas faltantes.
- La evidencia anterior señala protección en reposo pendiente para secretos MFA, conectores externos no configurados y aislamiento multi-tenant no verificado.
- Revisar privacidad del listado global de sesiones entregado a `audit.read`, alcance real de WORM y si los cambios de acceso invalidan indebidamente la configuración inicial de toda la instancia.
- Evaluar separar lectura, configuración y ejecución de agentes: `agents.write` agrupa acciones distintas. Una herramienta permitida por perfil también debe respetar la capacidad de negocio del ejecutor.

## 3. Trazabilidad: cómo se definirá cada operación

Se generará un inventario completo de routers, montajes, handlers de interfaz, formularios, botones, atajos, herramientas y trabajos. El catálogo siguiente es inicial; la fase 1 descubrirá y añadirá cada operación restante. Ninguna ruta queda cubierta sólo por pertenecer a un módulo.

Cada registro tendrá: ID; objetivo; superficie; actor y capacidades; recurso y propietario; precondiciones; entradas y límites; pasos; método/ruta/esquemas; autenticación/CSRF; respuesta y estados visibles; cambio persistente; evento de auditoría; confirmación; idempotencia; concurrencia; compensación; dependencia externa; casos positivos/negativos; estándar aplicable; prueba y evidencia; estado.

Estados de verificación: pendiente, aprobado, fallido, bloqueado por dependencia, no verificado o no aplicable con justificación. Para requisitos futuros se añadirá «no implementado», sin presentarlos como defectos de una función existente.

Para cada operación con efectos se exigirá la cadena: interacción en navegador → petición real → identidad y autorización → ejecución → lectura independiente del resultado → recarga/nueva sesión → auditoría. Los rechazos deben dejar recursos sin modificar. Se usarán datos sintéticos aislados y no se incluirán tokens, contraseñas ni secretos en evidencias.

## 4. Roles y capacidades

Se preservará inicialmente la matriz actual como línea base, sin ampliar permisos implícitamente. Se confrontará con las necesidades de negocio; discrepancias se documentarán antes de implementar cambios de política.

| Rol / cuenta manual | Casos autorizados principales | Negativos obligatorios |
|---|---|---|
| root / `root` | Todas las capacidades, configuración, identidad y auditoría | Otro usuario con etiqueta root no obtiene identidad raíz; confirmaciones siguen siendo obligatorias |
| platform_admin / `plataforma` | Configuración, servicios, módulos, IAM delegado, agentes; lectura datos/modelos; pronósticos, simulación y exportación | Secretos, importación/revisión de datos, entrenamiento/predicción/revisión de modelos fuera de su matriz; modificar root o cuentas fuera de delegación |
| security_admin / `seguridad` | Lectura configuración, IAM delegado, secretos, servicios y auditoría | Modificar configuración, módulos, entrenar, operar simulación o editar administradores superiores/pares fuera de alcance |
| data_engineer / `datos` | Leer/importar datos, leer modelos, auditoría y pronósticos | Aprobar datasets, entrenar, aprobar modelos, gestionar IAM o secretos |
| data_steward / `custodio` | Leer/revisar datasets y leer auditoría | Importación, entrenamiento, configuración o IAM |
| mlops_engineer / `mlops` | Datos y revisión, modelos/entrenamiento/predicción, agentes, módulos, pronósticos y simulación | Aprobación de modelos, IAM, secretos, configuración general y exportación no concedida |
| ml_reviewer / `revisor` | Lectura datos/modelos, revisión modelos y auditoría/verificación | Entrenar, importar, administrar o autoaprobar un artefacto propio |
| port_operator / `operador` | Lectura datasets/auditoría, pronósticos y simulación | Exportación no concedida, escritura datos/modelos e infraestructura |
| simulation_analyst / `simulacion` | Lectura datasets/auditoría, pronósticos, simulación y exportación | Administración, secretos, datos y modelos modificables |
| compliance_auditor / `auditor` | Lectura configuración/datasets/modelos, auditoría/verificación y revisión modelos | Modificar configuración, entrenar, secretos e IAM |
| api_consumer / `api` | Acceso básico y pronósticos | Catálogos restringidos, escritura, simulación, herramientas e IAM |
| readonly_viewer / `lector` | Consulta datos/modelos/pronósticos y capacidad de verificación declarada | Toda mutación; comprobar si la verificación concedida tiene una ruta/interfaz útil |
| Invitado | Sólo demostraciones identificadas expresamente | Gestión, acceso privado, ejecución con identidad de otra persona y efectos productivos |
| Rol personalizado / múltiples roles | Unión de capacidades autorizadas, con alcance sobre recursos | Autoescalamiento, capacidades desconocidas, roles revocados, acceso cruzado entre propietarios/tenants |

Se probará cada una de las 20 capacidades actuales: `workspace.read`, `config.read`, `config.write`, `iam.write`, `audit.read`, `audit.verify`, `secrets.write`, `services.write`, `agents.write`, `modules.write`, `datasets.read`, `datasets.write`, `datasets.review`, `models.read`, `models.train`, `models.predict`, `models.review`, `forecast.read`, `simulation.run`, `simulation.export`.

Además de sesiones normales: usuario inactivo, sesión expirada/revocada, cambio de rol durante operación, acceso directo por URL/API, cookie copiada, token de otro mecanismo, rol root sin indicador raíz, ausencia de rol/tablas y permisos contradictorios entre servidores. No se considerará suficiente ocultar un botón.

## 5. Catálogo inicial de casos de uso

Todas las filas incorporan los casos transversales de la sección 6. Las rutas exactas, payloads y postcondiciones se extraerán en fase 1, incluyendo las diferencias entre servidores.

| ID | Caso / pasos relevantes | Resultado a demostrar |
|---|---|---|
| AUTH-01 | Entrar, consultar perfil, navegar entre superficies y salir | Identidad coherente; cierre invalida sesión y no permite volver a recursos privados |
| AUTH-02 | Contraseña temporal → cerrar modal, recargar, URL directa → cambiar | Bloqueo persistente hasta completar requisito; rechazo de contraseña inválida/reutilizada; sesión conforme a política |
| AUTH-03 | MFA requerido → alta → código erróneo/válido → nuevo login | Factor sólo activado tras confirmar; desafío con expiración, límite de intentos y protección contra repetición |
| AUTH-04 | Recuperación/cambio de MFA, revocación y sesiones concurrentes | No bloqueo irreversible del administrador ni recuperación sin identidad verificada; flujo ausente se diseña antes de publicar |
| AUTH-05 | Cuentas manuales y demo bajo entornos local/producción | Excepción explícita y limitada; impedir su habilitación accidental en producción; conservar MFA activado |
| IAM-01 | Crear usuario con roles autorizados, confirmar y volver a entrar | Usuario persistente, auditoría, requisitos iniciales aplicados; duplicados y datos inválidos rechazados |
| IAM-02 | Cambiar roles/activar/desactivar, revocar y repetir petición | Cambios reales, sesiones afectadas invalidadas, operación duplicada sin efectos extra |
| IAM-03 | Crear/editar rol personalizado y combinar roles | Capacidades reconocidas, no autoescalamiento, límites de delegación aplicados en transacción |
| IAM-04 | Intentar cambiar root, propio rol y administrador superior | Rechazo en servidor y sin modificación; evento seguro de denegación |
| SETUP-01 | Instancia nueva → identidad → administradores → configuración → confirmar | Máquina de estados persistente; no omitir pasos cerrando interfaz; recuperación tras fallo/reinicio |
| CONFIG-01 | Editar puertos, paths, variables y nombre; validar/confirmar/guardar | Revisión persistente; conflicto concurrente; distinguir guardado de aplicación efectiva/reinicio |
| CONFIG-02 | Paths inválidos, traversal, puertos ocupados, variables prohibidas | Sin escritura fuera de ámbito ni configuración parcialmente aplicada; mensaje accionable |
| MODULE-01 | Habilitar/deshabilitar módulo y usar URL/API directa | Política definida por módulo; dependencias y efecto efectivo verificables, sin módulo visualmente apagado pero operativo |
| SECRET-01 | Alta/rotación/eliminación de llave, referencia y uso por conector | Valor protegido, no retornado ni registrado; referencia vigente y rotación efectiva; operaciones ausentes se delimitan |
| SECRET-02 | Clave ausente, corrupta, expirada o permisos insuficientes | Rechazo claro; no sustituir por secreto vacío ni ocultar fallo; restauración de bóveda probada |
| SERVICE-01 | Configurar endpoint/credencial, confirmar y diagnosticar | Separar configurado, alcanzable, autenticado, saludable y operativo; no equiparar HTTP 200 a integración completa |
| SERVICE-02 | Wazuh: autenticación → estado → consulta autorizada de agentes/eventos | Datos reales con trazabilidad, paginación y errores; ingesta/acciones sólo si forman parte del alcance definido |
| SERVICE-03 | Ollama/vLLM: catálogo → selección → inferencia → caída | Proveedor real, modelo disponible, salida válida, timeout y recuperación; ningún modelo inexistente seleccionable |
| SERVICE-04 | MLflow/MinIO: artefacto/experimento → guardar → recuperar | Referencias, integridad y permisos; probar TLS/credenciales, fallo parcial y reconexión |
| DATA-01 | Importar dataset válido, revisar esquema y consultar versión | Archivo real, tamaño/tipos/filas validados, checksum, versión, propietario y persistencia |
| DATA-02 | Dataset malformado, vacío, duplicado, gigante o con contenido hostil | Rechazo seguro y sin restos parciales; no ejecución de contenido ni escape de paths |
| DATA-03 | Evolucionar esquema, mapear campos, revisar impacto y versionar | Compatibilidad explícita con entrenamiento; migración sin sobrescribir versiones; diseñar función si no existe |
| DATA-04 | Custodio aprueba/rechaza versión y otro rol intenta hacerlo | Decisión/nota/autor registradas, versión correcta y autorización independiente de importación |
| DATA-05 | Lakehouse, fuentes, calidad, aranceles e historial/procedencia | Resultados respaldados por fuente/fecha; consultas restringidas; datos incompletos no presentados como cobertura total |
| ML-01 | Elegir versión dataset, receta/parámetros y entrenar | Ejecución real, semilla y partición, métricas, artefacto/checksum, duración y estado persistente |
| ML-02 | Cancelación, doble envío, recursos agotados y reinicio durante entrenamiento | Trabajo identificable; límites, reanudación o fallo terminal consistente; no artefacto parcial listo |
| ML-03 | Revisor independiente aprueba/rechaza; autor intenta aprobar | Separación de funciones, nota y checksum; aprobación local no equivale a despliegue productivo |
| ML-04 | Predicción con modelo/version y datos válidos/incorrectos | Inferencia real, contrato de columnas, métricas de ejecución y rechazo seguro |
| ML-05 | Registrar/desplegar/revertir modelo cuando corresponda | Endpoint efectivo, health y versión reales; rollback; bloquear o retirar controles si no hay capacidad operativa |
| FORECAST-01 | Terminal, horizonte y escenarios → calcular → comparar | Petición/resultado coherentes, unidades y bandas válidas; historial no confunde ejecuciones |
| SIM-01 | Escenario, horizonte y trayectorias → ejecutar → consultar auditoría | Actor desde servidor, cuotas, cálculo y registro reales; VaR/CVaR y unidades comprobados |
| SIM-02 | Límites, cancelación, timeout, recarga y concurrencia | Cotas de recursos; progreso/estado terminal; no repetir cobros ni aceptar respuesta vieja como actual |
| SIM-03 | Exportar y volver a importar/leer archivo | Contenido corresponde a ejecución autorizada, formato válido, metadatos; mitigación de fórmulas en CSV |
| AGENT-01 | Listar perfil, editar herramientas/estado/roles y guardar | Definición persistente; permisos por usuario/perfil/herramienta; no anunciar despliegue externo al guardar perfil local |
| AGENT-02 | Ejecutar herramienta permitida y rechazada | Esquema validado, identidad real, límites, salida verificable y auditoría; denegación sin efectos |
| AGENT-03 | Conversación → recuperación → llamada → respuesta | Historial aislado, fuentes visibles, cancelación, proveedor real; distinguir texto generado de acción ejecutada |
| AGENT-04 | Delegación entre agentes, entrega de resultado y fallo del receptor | Contrato de mensaje, correlación, destinatarios autorizados, límites de bucle, timeout y deduplicación |
| AGENT-05 | Prompt injection en usuario/documento/salida de herramienta | Texto no concede permisos ni cambia políticas; secretos y herramientas fuera de alcance protegidos |
| MCP-01 | Herramientas publicadas/registradas frente a ejecutables por perfil | Catálogo consistente; ocultas/denegadas/deshabilitadas tienen comportamiento explícito |
| AUDIT-01 | Consultar, filtrar y verificar registro/WORM | Actor, recurso, operación y resultado completos; manipulación detectada; no afirmar inmutabilidad externa sin probarla |
| AUDIT-02 | Escritura fallida de auditoría y exportación | Política de fallo definida para acciones críticas; no silencios ni filtraciones; exportación autorizada |
| OPS-01 | Health, instalación, migración, backup y restauración | Recuperación íntegra, compatibilidad de esquema y secretos; reinicio no pierde identidad/configuración |
| OPS-02 | Comprobar rutas/atajos legacy y enlaces del header/sidebar | Toda interacción lleva a operación vigente; ninguna llamada retirada sin recuperación clara |
| EXT-01 | Plugins, registro de runtimes, brain y extensibilidad | Inventariar activación/configuración/ejecución, dependencias y procedencia; entradas hostiles y autorización por método/ruta; ningún ejecutor elude la política central |
| PRIV-01 | Auditores/operadores consultan sesiones, telemetría y mensajes | Visibilidad justificada por rol/recurso, minimización de metadatos y retención; datos de otros usuarios no aparecen por permiso demasiado amplio |
| TENANT-01 | Propiedad de datasets/modelos/sesiones/mensajes y aislamiento | Si existe multi-tenant: pruebas cruzadas de IDOR/BOLA y storage. Si no existe: documentar límite y diseñar antes de ofrecerlo |

### Herramientas y comunicación

El catálogo MCP observado incluye `get_port_forecast`, `run_monte_carlo_risk_simulation`, `compare_model_benchmarks`, `simulate_external_feature`, `query_maritime_knowledge`, `lookup_panama_customs_tariff` y `validate_iso6346_container`. El panel de gestión expone como ejecutables sólo cuatro de ellas; se reconciliará catálogo, allowlist, backend y expectativas de interfaz.

Para cada herramienta se probarán esquema, capacidad del actor, permiso del perfil, módulo activo, cuota, cancelación, salida y evento. Para pronóstico: terminal/horizonte; riesgo: trayectorias/escenario/semilla; benchmarking: versiones y métricas; escenario externo: límites y etiqueta simulada; conocimiento/aranceles: fuente/fecha y ausencia de resultado; contenedores: códigos válidos/incorrectos y check digit.

La comunicación se modelará como creada → en cola → ejecutando → completada/fallida/cancelada/expirada. Cada mensaje/trabajo necesita ID de correlación, identidad, alcance, versión del contrato y plazo. El modelo no decide permisos. Si la aplicación carece de cola, streaming o comunicación interagente real, se registrará como función no implementada y se diseñará un adaptador concreto; no se simulará un éxito.

## 6. Escenarios transversales obligatorios

Para cada flujo aplicable: éxito con persistencia; validación; rol no autorizado; recurso ajeno; sesión expirada durante operación; cancelación antes/después de confirmar; doble clic/reintento; dos usuarios escribiendo la misma revisión; respuesta fuera de orden; red lenta/desconectada; 401/403/404/409/422/429/5xx; dependencia caída; recarga/cierre/reinicio; auditoría; accesibilidad y estado visual.

Pruebas de seguridad: XSS almacenado/reflejado/DOM, CSRF, CORS/origen a través del proxy, CSP, cookies/sesión/fijación, XSSI cuando aplique, IDOR/BOLA, escalamiento de roles, SSRF de conectores, path traversal, exposición de secretos/logs, archivos hostiles, límites de recursos y confirmaciones repetidas/expiradas/para otro payload. Análisis estático y dinámico se ejecutará sobre entorno aislado; cada hallazgo incluirá reproducción y prueba posterior.

Confirmaciones críticas deben mostrar actor, recurso, efecto y valores relevantes, caducar, ligarse a operación/payload/revisión y consumirse una sola vez. Validación, autorización, confirmación y mutación deben mantener consistencia transaccional. Se demostrarán carreras TOCTOU, rollback y conflictos sin cambios parciales.

## 7. QA de interfaces

Inventariar todos los estados: inicial, vacío, carga, listo, edición, validación, confirmación, guardado, error, sin permiso, expirado, cancelado y recuperación. Cada botón/select/atajo/enlace tendrá destino y resultado observables.

- Probar las tres superficies, enlaces directos, historial atrás/adelante, recarga y cambio de usuario.
- Unificar o adaptar explícitamente contratos de sesión/API; evitar colisiones entre servidores y hosts absolutos.
- Borradores y aviso de cambios pendientes en configuración, IAM, datasets, modelos, agentes y secretos; no persistir secretos en storage del navegador.
- Navegación fluida sin mostrar buffer anterior: cancelación o descarte por ID de petición, carga accesible y respeto de movimiento reducido.
- Sidebar por ratón, teclado y táctil: control descubrible, no dependiente sólo de hover; foco restaurado y área útil proporcional.
- Header, SVG, tarjetas, gráficos, formularios, notificaciones y diálogos en los 11 temas observados, incluidos todos sus estados.
- Viewports iniciales: 360, 390, 768, 1024, 1440 y 1920 px; zoom 200 %, reflow y textos largos ES/EN/PT.
- Chromium, Firefox y WebKit; emulación no reemplaza pruebas físicas, que quedarán identificadas si no se ejecutan.
- WCAG 2.2 AA: teclado/orden de foco, nombres y estados accesibles, lector de pantalla, contraste, errores y foco en diálogos, tamaño de objetivos. axe-core y revisión manual; escaneo limpio no constituye conformidad completa.

## 8. Fases, dependencias y entregables

| Fase | Trabajo previsto tras «Continuar» | Entregable / puerta de salida |
|---|---|---|
| 0. Preparar entorno | Snapshot privado, identificar procesos/configuración reales, aislar DB/vault/artifactos y fixtures; registrar límites de hardware/dependencias | Entorno reproducible y restauración probada; no pruebas destructivas contra datos reales |
| 1. Inventariar y especificar | Enumerar todos los endpoints y handlers de todas las apps; mapear roles/capacidades/casos/esquemas/propiedad | `operation-inventory`, `role-capability-matrix`, `use-cases`, `traceability`; 100 % de lo descubierto clasificado |
| 2. Identidad y seguridad P0 | Reproducir permisos, contratos de sesión, MFA, secretos, demo/producción, confirmaciones y carreras; corregir con regresión | Cero brechas confirmadas críticas/altas abiertas; rutas privadas explícitamente protegidas |
| 3. Contratos y UX P1 | Reconciliar superficies/rutas legacy, formularios reales, errores, borradores, carga/cancelación y temas | Cada interacción enlazada a contrato vigente; control no implementado claramente identificado |
| 4. Datos y modelos P1 | Importación/esquema/versiones/revisión; entrenamiento real; inferencia/revisión independiente; jobs y artefactos | Cadenas DATA y ML completas, persistentes y auditadas; separación de funciones |
| 5. Agentes e integraciones P1 | Perfil→herramienta→resultado; comunicación; guardrails; Wazuh/proveedores/MLflow/MinIO según disponibilidad | Ejecución real por conector disponible; pendientes por dependencia documentados, sin falsos éxitos |
| 6. Resiliencia, rendimiento y accesibilidad | Fallos de red/servicio, carga y concurrencia, backups, navegadores, 11 temas, teclado/lector | Informe de recuperación, accesibilidad y rendimiento con medidas reproducibles |
| 7. Aceptación y entrega | Reejecutar regresión afectada y E2E total, comparar inventario y evidencia; validar instancia que usará el usuario | Informe final por caso/rol/entorno, guía manual, riesgos abiertos y decisión de disponibilidad |

No se avanzará una funcionalidad como terminada si la dependencia necesaria está ausente. Se seguirá trabajando en las fases independientes, manteniendo el bloqueo visible.

## 9. Agentes y skills en la ejecución

El coordinador conserva inventario, prioridades y aceptación. Se usarán hasta tres agentes simultáneos además del coordinador, con archivos/tareas delimitados para evitar cambios contradictorios:

1. Identidad/AppSec: autenticación, matriz, límites de delegación, sesiones, confirmaciones y negativos.
2. Frontend/UX: contratos de interfaz, estados, temas, navegación y accesibilidad.
3. Flujos/integraciones: datos/modelos, herramientas/agentes, servicios y recuperación.

Cada agente entrega evidencia reproducible y propone correcciones acotadas. La verificación integrada la realiza el coordinador; los agentes no aprueban sus propios cambios sin regresión independiente. Trabajo paralelo de lectura y pruebas aisladas; cambios compartidos de autorización/esquema/API se coordinan secuencialmente.

Skills: `qa-infrastructure` para entorno, dependencias y aceptación; `network-api-ops` para contratos, proxy, errores y observabilidad; `agents` para capacidades de herramientas, ciclo de ejecución y comunicación. En implementación se aplicarán `python`/`go`/`ai` sólo cuando el trabajo concreto lo requiera, leyendo sus instrucciones antes de usarlas.

## 10. Estrategia de pruebas y evidencias

- Unitarias: políticas, validación, límites, estados, transformaciones y cálculo relevante.
- Integración: API real con DB/vault/artifactos aislados; transacciones, migraciones, revocación y concurrencia.
- Contratos: OpenAPI de cada servidor, petición/respuesta/error, payloads generados y consumidores frontend; mocks sólo para fallos controlados y pruebas explícitamente etiquetadas.
- E2E Playwright: cuentas separadas por rol; escribir datos válidos, recargar, consultar desde otra sesión y comprobar permisos/resultado/auditoría.
- Proveedores: prueba real cuando esté configurado, y pruebas de fallo reproducibles aparte. No contabilizar un mock como integración real.
- Visuales: capturas comparables por superficie/tema/viewport, estados de carga/error y revisión humana.
- Rendimiento: línea base repetible; objetivos iniciales de referencia LCP ≤2,5 s, INP ≤200 ms y CLS ≤0,1, con fuente/método y distinción laboratorio/campo. Presupuestos backend p95 por operación según hardware y línea base, no un umbral único para entrenamiento e inferencia.
- Seguridad: revisión, análisis estático/dependencias y dinámico en entorno aislado; cero filtraciones de secretos en resultados.

Cada defecto tendrá ID, severidad, caso, rol, entorno, pasos, esperado/observado, evidencia, causa, cambio, prueba y estado posterior. Prioridad P0: evasión de autorización/identidad, exposición de secretos, pérdida/corrupción crítica. P1: flujo principal roto, inconsistencia persistente o separación de funciones fallida. P2: recuperación, accesibilidad, diseño o rendimiento con impacto. La severidad depende del efecto reproducido, no sólo del nombre del componente.

## 11. Criterios finales de aceptación

1. Todas las rutas/interacciones descubiertas tienen clasificación, caso y política; ninguna privada queda sin decisión explícita.
2. Cada capacidad tiene al menos un éxito real y un rechazo probado cuando corresponda; cada rol tiene recorrido operativo válido y negativos relevantes.
3. Cada operación mutable publicada se prueba con datos válidos, persistencia tras recarga y comprobación de auditoría. Un 422 no cuenta como operación aprobada.
4. No quedan vulnerabilidades críticas/altas confirmadas sin corregir; MFA, setup y permisos no se evaden desde frontend ni API.
5. Ningún control anunciado como funcional responde sólo con una instrucción, catálogo o éxito simulado.
6. Estado, confirmación, errores, cancelación y recuperación son coherentes en frontend y servidor; respuestas antiguas no contaminan la vista actual.
7. Todos los temas/superficies previstos tienen revisión; incumplimientos AA aplicables registrados y resueltos antes de declarar conformidad.
8. Integraciones externas, despliegue de modelos, multi-tenant y pruebas físicas se aceptan únicamente con evidencia específica; en otro caso constan como pendientes/no implementados.
9. Regresión automatizada aprobada y procedimiento manual por rol reproducible; restauración y configuración efectiva verificadas.
10. Informe de cobertura con denominador del inventario, pendientes y bloqueos. No se inventa un porcentaje global ni se declara producción lista por aprobar la suite local.

## 12. Activación

La palabra **«Continuar»** autoriza iniciar la fase 0 y ejecutar este plan, con correcciones y verificaciones en el entorno de desarrollo. Hasta recibirla, no se instalarán dependencias, ejecutarán pruebas con efectos, modificarán permisos/credenciales/configuración ni reiniciarán servicios. Publicación o despliegue productivo no forma parte de esta activación.
