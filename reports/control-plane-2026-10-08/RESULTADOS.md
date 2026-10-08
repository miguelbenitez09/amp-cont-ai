# Corrección del espacio administrativo

Entrada: http://127.0.0.1:8000/static/workspace/index.html. Comparte sesión con /app. Las entradas antiguas del framework redirigen a este espacio.

## Implementado

- Cambio obligatorio de contraseña aplicado en el servidor y restaurado en el navegador; cerrar, Escape y recargar no desbloquean la sesión. Historial con salt permite impedir reutilizar contraseñas desde esta migración; registros antiguos sin salt no pueden reconstruirse.
- Retiradas con HTTP 410 las mutaciones bootstrap antiguas que podían emitir sesiones Root. Consultar el estado no crea usuarios y comprueba roles reales.
- Firma de sesión aleatoria persistente; invalida sesiones emitidas con la clave fija anterior. La contraseña y las cuentas existentes se conservaron.
- Usuarios, roles y capacidades específicas del espacio administrativo. Denegación en servidor, protección Root, límites a delegación y revocación de sesiones al modificar acceso.
- Configuración versionada de puertos, paths, variables permitidas y conectores. Borrador sin secretos, confirmación explícita, rechazo de conflictos y estado de configuración persistente. La finalización vuelve a comprobar la versión dentro de la transacción.
- Módulos locales de datasets, entrenamiento y agentes habilitables; cada servidor de módulo comprueba su estado.
- CSV numéricos y versiones de estructura, revisión obligatoria, entrenamiento local de media/regresión regularizada, partición temporal 80/20, métricas, SHA-256 e inferencia validada. TRAINING_MAX_ROWS controla realmente la importación.
- Perfiles de agentes con herramientas locales permitidas y ejecución confirmada. No hay resultados simulados presentados como llamadas a sistemas externos.
- Secretos cifrados mediante Fernet, escritura atómica y serializada en el proceso; valores nunca devueltos en inventario ni incluidos en confirmaciones/auditoría.
- Wazuh, Ollama, vLLM, MLflow y MinIO: configuración y diagnóstico HTTP real con timeout y TLS. Wazuh admite token o autenticación con usuario/contraseña guardados en la bóveda.
- Auditoría de gestión append-only con cadena de hashes; verificación independiente del registro operativo. Se eliminó la afirmación de certificación WORM del resultado del verificador.
- Logo SVG, nombres sencillos, fuentes mayores, seis temas, control de sidebar visible con hover/foco o en móvil, transiciones con aislamiento de respuestas tardías y respeto al movimiento reducido.

## Evidencia

Batería final: **95 pruebas aprobadas**, con dos avisos de dependencias WebSocket obsoletas. El login real de Root y su bloqueo por contraseña pendiente se comprobaron tras reiniciar la API; se cerró esa sesión de verificación sin cambiar la contraseña. Resumen: verification.json.

Las pruebas usan bases de identidad y bóvedas temporales. Comprueban permisos negativos, obligación de contraseña, ataques al flujo bootstrap, confirmaciones alteradas/reutilizadas, concurrencia, protección Root, cifrado, manipulación del registro y el flujo dataset → revisión → entrenamiento → checksum → inferencia. Playwright comprueba el diálogo original de /app, persistencia tras recarga, las nueve pantallas, cancelación/guardado y seis temas a 1440 y 390 píxeles. Capturas: management-desktop.png y management-mobile.png.

La instancia local respondió HTTP 200 para el espacio administrativo, sesión pública, guardia de sesión y SVG. Las dos mutaciones bootstrap retiradas respondieron 410. Root conserva la obligación de cambio de contraseña. Se actualizó la API local; no se cambió su contraseña para probar.

## Límites verificados y pendientes

- Guardar puertos no mueve listeners activos. scripts/start_configured_instance.py --dry-run valida el plan; el mismo lanzador inicia gateway y API usando la configuración guardada después de detener la instancia anterior. Crea los directorios configurados y expone sus paths al proceso. Datasets y modelos del flujo local se conservan en SQLite; no se migran automáticamente a archivos o almacenamiento distribuido.
- No se dispone de evidencia de despliegue o credenciales reales de Wazuh/MinIO/proveedores. Su conectividad externa, ingesta y agentes desplegados permanecen no verificados.
- Los agentes implementados son perfiles con herramientas locales, no una plataforma de despliegue distribuido. Los modelos soportados son las dos recetas locales descritas, no todos los entrenamientos posibles de Fabric/Databricks.
- Append-only y hashes detectan modificaciones; un administrador del almacenamiento puede eliminar o reemplazar la base. Retención WORM certificada requiere almacenamiento externo y políticas verificables.
- Las claves locales de bóveda y firma requieren protección/backup mediante ACL del sistema operativo. No se verificó protección contra administradores locales ni concurrencia de múltiples procesos que escriban la bóveda.
- No se declara conformidad integral ASVS/WSTG/WCAG ni preparación para producción: faltan evaluación completa de accesibilidad con lectores de pantalla, otros navegadores, límites multi-tenant y verificación de todos los servicios externos y rutas heredadas.
