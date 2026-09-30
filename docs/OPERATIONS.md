# Operación y recuperación

Comprueba `GET /health` para disponibilidad y `GET /api/status` para modo, versión y servicios. Las respuestas de la interfaz reflejan esas APIs y no inventan métricas.

Los backups se crean con `POST /api/backups` usando el permiso `backups:write`. Cada copia registra SHA-256 y fecha. La restauración nunca sobrescribe la base activa: debe hacerse sobre un destino nuevo y validarse antes del cambio operativo.

El audit log tiene triggers SQLite que bloquean UPDATE y DELETE desde la aplicación. La garantía es de trazabilidad de aplicación; el propietario del archivo SQLite todavía puede modificarlo fuera del proceso, por lo que los backups y controles de acceso al volumen son parte de la operación.

Antes de un release ejecuta:

```bash
python scripts/verify_public_release.py --root .
python scripts/build_public_release.py --output .artifacts/amp-cont-ai-public.zip
```

El verificador aplica la lista allowlist y bloquea scrapers, datos crudos, bases, secretos y módulos legacy.
