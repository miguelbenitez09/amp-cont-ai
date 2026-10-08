# Plan de implementación del espacio de gestión

## Brechas confirmadas

1. Estado de cambio obligatorio descartado por sincronizaciones duplicadas; cerrar el diálogo permite volver a la vista operativa.
2. Dos identidades incompatibles: cookies portops_session y amp_session, bases de datos y capacidades diferentes.
3. Paneles de instalación y configuración no forman un espacio de trabajo accesible tras iniciar sesión.
4. Secretos locales con ofuscación XOR y clave fija; no es cifrado apto para almacenar credenciales.
5. Capacidades publicitadas sin flujo completo de importar, revisar, versionar, entrenar y verificar artefactos en la aplicación activa.
6. Estado y efectos de conectores/configuración poco claros; guardar no demuestra conectividad ni reconfigura listeners.

## Secuencia y criterios de aceptación

1. Identidad: servidor bloquea todas las APIs operativas para una cuenta con cambio pendiente; me, cambio y logout siguen accesibles. Navegador restaura obligación después de recargar; Escape y cerrar no evaden el estado. Prueba con base temporal.
2. Espacio de gestión integrado: misma sesión y permisos, navegación visible según capacidades, servidor exige permiso específico en cada recurso. Estado persistente de instalación con etapas derivadas de registros reales.
3. Configuración: valores versionados y persistentes, validación, confirmación antes de aplicar; conflictos de versión no sobrescriben cambios. Puertos y paths se guardan como configuración deseada, con necesidad explícita de reinicio cuando corresponde. Conectores tienen prueba real de red, límite de espera y controles de destino.
4. IAM y auditoría: gestionar cuentas/roles/permisos, evitar retirar el último root, revocar sesiones al cambiar acceso, confirmación vinculada a actor y operación. Registro append-only encadenado, verificación de integridad sin afirmar protección contra un administrador del archivo.
5. Datos y modelos: importación CSV numérica controlada, versiones de esquema/datos, revisión obligatoria, entrenamiento real local de recetas soportadas, métricas temporales, checksum, inferencia con firma verificada. Sin prometer entrenamientos distribuidos inexistentes.
6. Agentes y servicios: configuración persistente, herramientas permitidas verificadas, Wazuh/proveedores con diagnóstico real. Ninguna ejecución de shell ni exposición de secretos.
7. UI: header usa SVG del proyecto; fuentes y nombres sencillos; navegación con control que aparece al acercar el puntero y siempre accesible por teclado/móvil. Todas las paletas mantienen contraste.
8. Verificación: pruebas negativas de autorización, flujo de cambio/reanudación, confirmaciones, conflictos, secretos, integridad, dataset→entrenamiento→inferencia y navegación real. Registrar límites de servicios externos no instalados.

## Alcance operativo

Se reutiliza el motor local ModelService existente y la identidad de la aplicación activa. La nueva configuración se conserva en el almacenamiento local del control plane. Cambios de listeners y despliegues de servicios externos requieren reiniciar/configurar esos procesos; la UI lo informa y no ejecuta comandos del sistema.
