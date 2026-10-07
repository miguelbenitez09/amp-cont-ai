# Estado de implementación

Este documento registra evidencia verificable de los ciclos ejecutados. Una
capacidad se marca como cerrada solo cuando el código, las pruebas y el flujo
real coinciden.

## Ciclo 0 — diagnóstico y contratos

- Se inspeccionaron las 34 observaciones de interfaz y los flujos de ANA,
  autenticación, RAG, liquidación e ISO 6346.
- Se identificó que `status=1` del catálogo ANA indica una referencia activa,
  no vigencia legal.
- Se separaron artefactos Bronze, transformaciones Silver y resultados Gold.
- Los documentos alternativos se descargan en un área de recuperación con
  hash y URL original; no sustituyen silenciosamente una referencia ANA.

## Ciclo 1 — estados reales de cálculo e interfaz

Implementado y probado:

- La calculadora no inventa CIF, ITBMS, tasa DUA, permisos ni totales.
- Los resultados ausentes aparecen como `N/D`.
- Los diagnósticos residuales de la interfaz también parten de `N/D` y sólo
  muestran valores cuando la API entrega un artefacto de evaluación registrado.
- El endpoint de liquidación requiere código HS y CIF explícitos.
- ISO 6346 acepta alfabeto ASCII válido y no inventa datos de buque,
  sello, terminal o peso.
- Se añadieron tokens responsive, foco visible, reducción de movimiento,
  objetivos táctiles y tablas desplazables.
- Se retiraron etiquetas que afirmaban “Zero Mocks”, “100% Operational” o
  reproducibilidad universal sin evidencia de ejecución.

Evidencia:

- La ejecución completa supervisada más reciente terminó en `198 passed, 1 skipped, 1 warning`
  en 75,22 s. La advertencia proviene de la detección de núcleos físicos de
  `joblib` en Windows y no afecta el resultado de las pruebas.
- `node --check` correcto para los scripts principales del navegador.
- 28 pruebas focalizadas de RAG, ISO y sincronización ANA aprobadas.
- Smoke visual Playwright en `/app` a 390×844: sin overflow horizontal, selector
  ES/EN/PT operativo y búsqueda aduanera presente.
- El smoke también cubre una liquidación con regla candidata: la UI muestra
  “Liquidación bloqueada” y el siguiente paso documental en lugar de ocultar el
  motivo detrás de un `HTTP 422`.
- La comparación de las 10 fuentes PDF oficiales alternativas produjo 36.263
  filas de códigos, 27.440 códigos distintos y 12.904 códigos observados
  también en importaciones. El resultado está en `data/gold/recovery_import_comparison`
  y conserva hash, URL, documento y tipo de evidencia.

## Ciclo 2 — reanudación, procedencia e i18n

- Se reanudó el staging ANA `20260930T070226Z` con hash incremental, archivos
  temporales por documento y `checkpoint.json`; se conservaron 616 documentos
  únicos y se reintentaron los 17 fallos.
- Los 17 fallos siguen respondiendo HTTP 404 tras reintentos. No se creó
  `CURRENT`: una ejecución incompleta no sustituye una versión válida.
  `data/gold/ana_agreements_recovery/source_register.json` conserva categoría,
  título, URL, fecha, alternativa oficial y nivel de certeza para revisión manual.
- La CLI acepta `--resume-run-id`; la publicación atómica sigue condicionada a
  `complete=true`.
- Las claves de cobertura de traducción se materializan en grupos nativos al
  arranque y el auditor `node scripts/validate_i18n.js` exige 201 rutas presentes
  en ES, EN y PT. Se eliminó el fallback de alias dentro del motor de traducción.
- La calculadora, el validador ISO y la búsqueda ya no se inicializan con HS,
  CIF, contenedor, buque, precinto o terminal inventados; los campos faltantes
  muestran `N/D` y requieren una acción explícita.
- Las reglas arancelarias curadas sin documento ANA enlazado se marcan como
  `pending_document_evidence`; la API devuelve 422 y la interfaz deshabilita
  “Liquidar” hasta que exista evidencia documental verificable.
- Se actualizaron los query strings de los bundles estáticos para que el navegador
  no conserve la versión anterior; la prueba en `/app` cargó `customs_rag.js?v=1.0.1`,
  mantuvo los tres campos vacíos y mostró la validación `Completa un código HS y un
  valor CIF mayor que cero.`.
- `scripts/ui_smoke_playwright.py` valida `/app` en 390×844, 768×1024 y 1440×900:
  cero overflow horizontal, tres idiomas, ocho filtros rápidos, rechazo de entradas
  vacías, ausencia de `undefined` visible, etiqueta de fuentes traducida en los tres
  idiomas y estado operativo servido por `/health`.
- Las rutas `/api/v1/auth/users` ahora exigen sesión y rol `root`,
  `platform_admin` o `security_admin`; el invitado recibe 401. La contraseña de
  creación de usuarios es obligatoria y tiene longitud mínima de 12 caracteres.
  La validación de integración posterior al cambio terminó en `38 passed` con
  el servicio local disponible; la suite completa posterior terminó en
  `195 passed, 1 skipped`.
- Los KPI de calidad, guardrails, satisfacción y latencia ya no muestran 100%,
  5.0 o cero como valores iniciales; el backend devuelve `null` sin observaciones
  y la interfaz presenta `N/D` hasta disponer de una medición.
- Verificación runtime tras reiniciar Uvicorn: `GET /api/v1/auth/users` sin
  credenciales devuelve `401`; `/health` devuelve `healthy`; el smoke responsive
  final permanece en `passed: true`.
- La revisión de fuentes alternas descargó 22 referencias oficiales relacionadas
  sin modificar los RAW ANA: 9 tienen alternativa exacta, 7 repositorios
  relacionados y 1 es una alternativa candidata que requiere confirmar el país
  del tratado. Ya no queda una referencia sin URL oficial candidata ni una
  clasificación de confirmación manual en el registro; la candidata no se
  habilita como evidencia legal hasta confirmar la correspondencia documental.
  El Apéndice 1 del Anexo XVI EFTA/Costa Rica quedó enlazado al PDF oficial de
  MICI y conserva el tipo de acuerdo regional en el registro.
- `scripts/probe_ana_missing_variants.py` probó de forma secuencial las rutas
  originales, extensiones, host alterno y variantes de nombre de los 17 fallos:
  no encontró ningún PDF original (`successful_variants=0`). El resultado se
  conserva en `data/gold/ana_missing_variant_probe.json` y no modificó Bronze.
  El reporte clasifica las 17 referencias como
  `resource_not_found_at_probed_variants`; no observó respuestas 401, 403 ni
  429, por lo que no hay evidencia de bloqueo o baneo en esta comprobación.
- `data/gold/ana_missing_references_report.json` consolida cada referencia para
  revisión manual con categoría, subcategoría, título, URL, variantes probadas e
  interpretación, y declara `raw_inputs_modified=false`.
- Una búsqueda adicional por nombre exacto en fuentes web no produjo resultados
  oficiales verificables para esas referencias; los resultados de terceros se
  excluyeron del catálogo y no se trataron como sustitutos documentales.
- `tests/test_ana_source_manifest_consistency.py` verifica que el manifiesto vivo
  conservado en Gold coincide byte a byte con el SHA-256 que Bronze registró y
  mantiene las 700 referencias inventariadas.
- `scripts/extract_agreement_chronology.py` genera evidencia literal de fechas y
  años para 13 PDFs oficiales de recuperación: 750 filas con página y
  fragmento, sin inferir vigencia legal. El resultado está en
  `data/gold/ana_agreements_recovery/chronology/`.
  También se incorporó el portal interactivo oficial del Arancel Nacional como
  fuente HTML navegable. El PDF directo del arancel respondió 404/timeout, por
  lo que permanece registrado como no descargado y no habilita evidencia legal.
  localizada. Las cuatro convocatorias TPC-PLL/PS 2014, 2017, 2018 y 2019 y el
  Capítulo 10 Chile–Panamá se conservaron con SHA-256 en
  `data/bronze/ana_recovery_sources/manifest.json`.
- El comparador ahora exige evidencia por fila: el reporte derivado cubre 10 PDFs,
  36.263 filas, y confirma página y fragmento textual para el 100% de las filas
  (`evidence_coverage_complete=true`).
- El probe del API interactivo ANA responde 200 para `27101921`, pero devuelve
  la subpartida `271019210000` como diésel para vehículos y no como bunker VLSFO;
  por eso no se promovió la regla curada `2710.19.21.00.00`. La respuesta
  resumida queda en `data/gold/ana_tariff_portal_probe.json` con entidades y nota
  legal referenciada.
- La comparación secuencial de las 17 subpartidas curadas contra el API oficial
  encontró 7 coincidencias de código y descripción, 2 coincidencias de código
  con descripción incompatible (incluido bunker VLSFO frente a diésel), y 9
  códigos no encontrados. El reporte queda en
  `data/gold/ana_portal_catalog_comparison.json`; ninguna discrepancia actualiza
  automáticamente el catálogo.
- Se añadió la transformación Silver `ana_agreements_catalog.parquet`: normaliza
  los 700 registros del staging, relaciona los 17 fallos con su registro de
  recuperación y mantiene `publication_ready=false` mientras el manifiesto ANA
  no sea completo. No copia ni modifica los documentos Bronze.
- El catálogo aduanero expone `regulatory_entity_sources` para las entidades
  AMP, MiAmbiente, SNE, MIDA, MINSA, APA y demás códigos usados; cada enlace se
  etiqueta como punto institucional de navegación y no como prueba automática
  de que el permiso aplique a la partida.
- Se eliminó una credencial fija de los ejemplos de API del navegador: los
  snippets Bearer ahora exigen `AMP_API_SECRET_KEY` desde el entorno o un gestor
  de secretos y no contienen un valor operativo reutilizable.
- El benchmark ya no devuelve un ganador fijo en sus endpoints: expone
  `selection_recommendation` calculado por `lowest_avg_wape_then_latency` y
  marca `requires_governance_promotion=true`; en la medición actual el candidato
  es Random Forest, mientras el estado de producción no se cambia automáticamente.
- La vista comparativa ya no presenta métricas, latencias ni un Champion antes
  de recibir la respuesta del benchmark; inicia en `N/D` y sólo pinta valores
  registrados por la API. El smoke responsive posterior continuó pasando en
  390, 768 y 1440 píxeles.
- Las exportaciones de pronósticos y la ficha de procedencia ya exponen el
  candidato y sus métricas desde la política de selección registrada, sin
  escribir un modelo Champion ni WAPE/R² fijos en el resultado exportado.
- Las tarjetas de diagnóstico, explicación WAPE y modo de ejecución tampoco
  muestran R², precisión o latencia históricos antes de recibir mediciones; sus
  valores iniciales son `N/D` y el smoke visual sigue pasando.
- Verificación runtime posterior al reinicio: la exportación de pronósticos
  devuelve `modelo_seleccionado=random_forest`, la política
  `lowest_avg_wape_then_latency` y no incluye el campo legado `modelo_champion`.
- `scripts/audit_master_plan.py` genera `data/gold/master_plan_audit.json` y
  verifica que existan artefactos para las nueve fases MLOps. El reporte separa
  cobertura de artefactos de cierre real. `scripts/validation/run.py` conserva
  ahora `data/gold/validation/latest.json` con salud runtime y la suite completa:
  ambas pasan, pero `plan_phase_closure_ready=false` porque el Bronze ANA no está
  completo y Silver no es publicable.
- `data/gold/master_plan_audit.json` expone también el conteo y clasificación del
  reporte de referencias faltantes para que el bloqueo de publicación sea auditable.
- `scripts/publish_ana_snapshot.py` implementa la barrera atómica de `CURRENT`:
  rechaza manifiestos incompletos y sólo escribe el puntero después de validar
  `complete=true`, cero fallos y `publication_ready=true` en Silver.
- La API ahora expone `GET /api/v1/data/ana/status`, de solo lectura, con el
  `run_id`, registros descargados/fallidos, estado de completitud, publicación
  Silver, recuperación de fuentes y relación de procedencia. El estado runtime
  actual es `staging_incomplete` (700 registros, 683 descargados, 17 fallos),
  por lo que la interfaz puede distinguir un snapshot incompleto de un catálogo
  publicado sin presentar disponibilidad aparente.
- Ese endpoint incluye `missing_references` con la ruta del reporte manual y sus
  clasificaciones, sin exponer los fallos como una sustitución del catálogo.
- También incluye `current_snapshot`, que sólo se marca disponible cuando el gate
  atómico ha creado `data/bronze/ana_agreements_full/CURRENT`.
- La suite de modelos consume primero `models/model_benchmark.json`, el artefacto
  generado por entrenamiento, y adjunta su ruta como evidencia en cada candidato.
  La selección sigue siendo una recomendación gobernada y no cambia el modelo de
  producción automáticamente; los valores de respaldo sólo aplican en un checkout
  sin artefacto.
- La tarjeta Lakehouse ya no afirma “17 autorizadas” ni “Manifiesto verificado”:
  consulta `/api/v1/data/ana/status`, muestra descargados/total y marca los
  fallos antes de publicación. Las etiquetas tienen traducción nativa en ES, EN y
  PT; el smoke responsive volvió a pasar en 390, 768 y 1440 píxeles.
- Las fichas de procedimientos aduaneros ahora traducen sus encabezados y
  muestran explícitamente si son evidencia documental verificada, observación
  histórica o regla candidata pendiente. Las reglas candidatas mantienen la
  liquidación bloqueada y advierten que el texto no prueba vigencia legal.
- Los endpoints mutables de secretos, pruebas de proveedores, guardrails y
  registro/despliegue de modelos ahora requieren autenticación y un rol de
  plataforma permitido en servidor; una petición anónima devuelve 401 antes de
  ejecutar cualquier mutación. La prueba de integración cubre los seis flujos.
- La inicialización de root ya no es una operación pública: exige un usuario
  administrativo o `PORTOPS_INSTALL_SECRET` mediante `X-Install-Secret` cuando
  el secreto de instalación está configurado. El endpoint conserva el flujo de
  bootstrap, pero deja de permitir una llamada anónima que cree o verifique root.
- Las CLI `scripts/bootstrap_platform.py` y `scripts/evaluate.py` dejaron de
  imprimir un Champion fijo, valores de respaldo o invariantes cuantílicas como
  hechos verificados. Ahora leen la recomendación y métricas del artefacto; las
  invariantes aparecen como pendientes si no existe un reporte de evaluación.
- El HUD de seguridad ya no presenta `31/31 Permisos Otorgados`; muestra el
  conteo de permisos recibido desde la sesión activa y `N/D` cuando aún no hay
  una respuesta autenticada. El smoke responsive confirmó que no reaparecen
  cifras estáticas de permisos.
- El panel de Quality Gates ya no inicia con scores `1.00`, cero cuarentenas ni
  “Todos los Gates Activos”. Arranca en `N/D` y consulta el resumen real de
  calidad, puertos y cuarentena; sólo después de una respuesta del servicio
  muestra la medición correspondiente.
- La matriz visual de despliegue también inicia sus seis comprobaciones en
  `N/D`; sólo el endpoint de verificación en vivo puede convertirlas en PASS,
  WARN o FAIL.
- El HUD IAM inicia en `N/D` y modo invitado; sólo después de consultar la sesión
  reemplaza usuario, rol, permisos y tipo de autenticación con datos reales.
- La cobertura histórica del hero, benchmark y procedencia ya no está codificada
  como “140 meses”: inicia en `N/D` y se rellena desde el manifest temporal del
  dataset (`months_count`, inicio y fin observados).
- Se eliminó también la repetición de “140 meses” en la documentación OpenAPI,
  descripciones metodológicas y fichas de i18n; cualquier cobertura o métrica
  debe proceder del manifest o del reporte de evaluación correspondiente.
- La auditoría de seguridad eliminó contraseñas compartidas embebidas en la API,
  el panel de administración y el formulario de primer arranque. Las cuentas
  nuevas reciben una credencial aleatoria de un solo uso cuando el operador no
  proporciona una, y el cambio inicial sigue siendo obligatorio.
- La liquidación fiscal ahora traduce el 422 de una regla candidata a un estado
  visible y accionable: explica que falta evidencia documental y bloquea el
  cálculo reproducible hasta clasificar una regla ANA vigente.
- La navegación principal conserva todos sus elementos accesibles mediante
  desplazamiento táctil, rueda y una barra de desplazamiento visible. Los
  distintivos de capacidades muestran un icono grande separado de su etiqueta,
  y los badges de Ley, autoría y licencia navegan a sus secciones reales.
- Las tarjetas ISO abren una ficha modal proporcional con explicación técnica,
  evidencia y botón de auditoría; ese botón cierra la ficha, activa IAM/WORM y
  enfoca la sección de controles. El login del encabezado abre el centro IAM.
- La latencia del encabezado se mide contra `/health` cada 15 segundos y queda
  marcada con hora de medición; no se presenta como un valor fijo.
- La suite final quedó en 198 pruebas aprobadas, 1 omitida y 1 advertencia de
  entorno Windows; el smoke UI pasó en 390, 768 y 1440 píxeles.

## Trabajo abierto

- Completar traducciones nativas ES/EN/PT en todos los componentes dinámicos.
- Resolver el flujo visual completo de las observaciones 1–34 con Playwright.
- Añadir páginas y fragmentos de evidencia al comparador ANA–importaciones.
- Completar autorización servidor para cada panel administrativo.
- Extraer procedimientos, modificaciones y cronología con revisión de
  calidad; una coincidencia numérica de un PDF no certifica un código legal.
- Publicar el snapshot ANA sólo cuando `/api/v1/data/ana/status` informe
  `published=true`; mientras existan fallos, el manifiesto queda en staging y
  las fuentes de recuperación se mantienen como evidencia relacionada.
- Completar el flujo visual de las observaciones 1–34 con Playwright y cubrir
  errores de API, teclado y permisos.
- Completar autorización servidor para cada panel administrativo.
- Extraer procedimientos, modificaciones y cronología con revisión de calidad;
  una coincidencia numérica de un PDF no certifica un código legal.

## Regla de aceptación

Un estado de interfaz debe proceder de una respuesta de servicio, una medida
registrada o un manifiesto verificable. Los textos históricos, las tasas sin
fuente y las referencias no localizadas permanecen etiquetados como tales.
