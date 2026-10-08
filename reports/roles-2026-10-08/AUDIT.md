# Auditoría de roles y acceso — 8 de octubre de 2026

## Alcance y evidencia

Instancia local: http://127.0.0.1:8000/static/workspace/ y área operativa /app.
Se verificaron los 12 roles incorporados, sus capacidades efectivas, navegación, formularios y rechazos del servidor. Esto no constituye una certificación completa ASVS/WCAG ni una verificación de todas las integraciones externas.

- `live-matrix.json`: 12 cuentas reales, inicio/cierre de sesión y 96 comprobaciones de acceso.
- `live-browser-matrix.json`: Chromium, 12 cuentas, 64 pantallas de gestión, sin excepciones JavaScript.
- `browser-matrix.json`: controles de acción y navegación operativa por rol; persistencia y confirmación de MFA con código real.
- `tests.xml`: resultado de la regresión automatizada; bases de identidad aisladas.
- Capturas `*-workspace.png`: estado visual de cada cuenta local.
- Pruebas Go del gateway: documentos de gestión, políticas de origen y seguridad del proxy.

## Correcciones

1. Una única matriz de capacidades gobierna autorización del servidor, permisos de sesión e interfaces. Un nombre de rol root sin identidad raíz no concede privilegios.
2. Se restringió la delegación: los administradores no modifican cuentas superiores, pares con privilegios fuera de su alcance, el usuario raíz ni sus propios roles.
3. Las rutas administrativas antiguas que omitían confirmaciones se retiraron; las modificaciones pasan por los formularios confirmados del panel de gestión.
4. MFA obligatorio conserva el bloqueo al recargar. La generación del secreto no activa el factor: exige un código válido; el alta revoca sesiones previas.
5. Los cambios de acceso revocan sesiones; permisos de múltiples roles se calculan desde los datos actuales.
6. Importar y revisar datasets son permisos separados. Entrenar y revisar modelos son permisos separados. El autor del entrenamiento no puede aprobar su propio modelo.
7. La simulación usa la identidad autenticada del servidor, no un usuario elegido por el cliente.
8. El gateway entrega el documento correcto tanto para `/static/workspace/` como para `/static/workspace/index.html`, sin redirigir al área operativa.
9. La navegación espera las capacidades de la sesión y descarta respuestas de otro usuario. Se restauran las opciones públicas al cerrar sesión.
10. Las pruebas de navegador usan también la migración real de telemetría, evitando una base de prueba incompleta.

## Cuentas manuales

| Usuario | Rol | Alcance principal |
|---|---|---|
| root | root | Administración completa |
| plataforma | platform_admin | Instancia, módulos, servicios y usuarios subordinados |
| seguridad | security_admin | IAM, secretos, servicios y auditoría |
| datos | data_engineer | Lectura e importación de datasets |
| custodio | data_steward | Revisión de datasets |
| mlops | mlops_engineer | Entrenamiento, inferencia, agentes y módulos |
| revisor | ml_reviewer | Revisión independiente de modelos |
| operador | port_operator | Pronósticos y simulación |
| simulacion | simulation_analyst | Simulación y exportación |
| auditor | compliance_auditor | Auditoría, lectura de configuración y revisión de modelos |
| api | api_consumer | Pronósticos |
| lector | readonly_viewer | Consulta de datasets, modelos y pronósticos |

Las capacidades exactas por rol constan en `browser-matrix.json`; esta tabla resume el alcance y no sustituye esa matriz.

La contraseña solicitada se entrega en la conversación y en `.bootstrap/manual-role-credentials.txt` (archivo privado ignorado por Git). Estas cuentas están marcadas exclusivamente para pruebas locales: el servidor rechaza su uso remoto, incluso con una sesión copiada. La excepción de alta inicial de MFA sólo corresponde a estas cuentas marcadas; no elimina un factor ya activado. Se preservaron otras cuentas y se hizo una copia privada de la base antes de restablecer las credenciales. Las sesiones anteriores de las cuentas modificadas fueron revocadas.

## Límites de verificación

- Wazuh, Ollama, vLLM, MLflow y MinIO no tienen conectores configurados en esta instancia: no se afirma conectividad ni ejecución real contra esos servicios.
- El entrenamiento y la revisión se verificaron localmente. No se verificó despliegue de modelos a producción.
- Navegador probado: Chromium. Firefox, WebKit, lectores de pantalla y conformidad WCAG 2.2 AA completa: no verificados en esta ronda.
- No se verificó aislamiento multi-tenant ni infraestructura distribuida comparable a Fabric/Databricks.
- Los secretos de MFA en la base de identidad requieren una revisión adicional de protección en reposo antes de declarar producción lista.
- La demostración anónima mantiene sus rutas públicas limitadas; las cuentas autenticadas quedan sujetas a sus capacidades.

## Resultado final

Regresión: 115 pruebas aprobadas, 0 fallidas; 2 avisos de obsolescencia de dependencias WebSocket. Las pruebas Go del gateway también aprobaron. Instancia real: 12 cuentas, 96 comprobaciones de acceso y 64 pantallas verificadas sin excepciones JavaScript.

