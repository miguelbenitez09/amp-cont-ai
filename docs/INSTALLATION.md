# Instalación del Framework AMP-CONT-AI

La distribución pública instala una instancia local del framework. Incluye la interfaz, la API, el esquema SQLite, recetas de referencia y validación de datasets. No incluye scrapers privados, credenciales, bases de datos ni datos crudos.

## Requisitos

- Python 3.12 o superior.
- Windows, Linux o macOS.
- La primera ejecución usa únicamente `127.0.0.1`.

Desde la raíz clonada:

```bash
python -m venv .venv
python scripts/install.py --install --mode portal
python scripts/install.py --mode portal
```

El modo `portal` muestra la documentación del proyecto y no crea usuarios ni habilita capacidades administrativas. Para crear una instancia operativa:

```bash
python scripts/install.py --install --mode framework --no-start
python scripts/install.py --mode framework
```

El instalador crea `.local/framework`, genera un usuario `root` temporal y escribe `bootstrap-credentials.json` en ese directorio. Lee el archivo una sola vez, inicia sesión y cambia la contraseña desde la interfaz o `POST /api/auth/password`. La contraseña nueva debe tener al menos 15 caracteres. Después crea exactamente los tres roles iniciales (`sysadmin`, `secopsadmin`, `mlopsadmin`) desde Configuración de instancia.

## Variables

Copia `.env.example` a un archivo local si necesitas conservar la configuración:

```dotenv
AMP_MODE=framework
AMP_HOST=127.0.0.1
AMP_PORT=8000
AMP_STATE_DIR=.local/framework
AMP_SECURE_COOKIES=false
AMP_SESSION_HOURS=8
```

El instalador rechaza hosts públicos en una instalación local y rechaza cualquier estado dentro de `C:\Users\mbeni\Downloads\datasets\_imports` o `_exports`. Esas rutas están reservadas para procesos de adquisición activos y nunca son utilizadas por el framework.

## Docker

`docker compose up --build` expone el servicio solamente en `127.0.0.1:8000` y persiste el estado en el volumen `framework_state`. Cambia los secretos y publica detrás de un proxy TLS únicamente después de revisar la configuración de seguridad.
