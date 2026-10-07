# Panamá PortOps-AI v1.0.0 — despliegue seguro de referencia

Este proyecto sirve la interfaz operacional desde FastAPI/ASGI para mantener un gateway liviano y auditable. No requiere Node.js en producción para renderizar la aplicación. Node queda reservado para validación estática de JavaScript y, si en el futuro se agregan dependencias frontend, el gestor permitido es `pnpm`.

## Gateway HTTP

El gateway aplica cabeceras de seguridad en cada respuesta:

- `Content-Security-Policy` con origen propio, bloqueo de objetos, `frame-ancestors 'none'` y permisos explícitos para los assets usados por la interfaz.
- `X-Frame-Options: DENY` para impedir clickjacking en navegadores heredados.
- `X-Content-Type-Options: nosniff` para evitar interpretación ambigua de MIME.
- `Referrer-Policy: strict-origin-when-cross-origin`.
- `Permissions-Policy` bloqueando cámara, micrófono, geolocalización, pagos y USB.
- `Cross-Origin-Opener-Policy` y `Cross-Origin-Resource-Policy` en modo `same-origin`.
- `Cache-Control: no-store` en `/app` y `/api/*`.

Las cookies de sesión se emiten con `HttpOnly`, `SameSite=Lax` y `Path=/`. El atributo `Secure` se activa automáticamente cuando la petición llega por HTTPS, cuando el reverse proxy envía `X-Forwarded-Proto: https`, o cuando se define `PORTOPS_SECURE_COOKIES=1`.

## TLS recomendado

Para producción se recomienda terminar TLS en un reverse proxy pequeño y abierto como Caddy o Nginx. Ejemplo con Caddy:

```caddyfile
portops.example.org {
  reverse_proxy 127.0.0.1:8000 {
    header_up X-Forwarded-Proto https
    header_up X-Forwarded-For {remote_host}
    header_up X-Forwarded-Host {host}
  }
}
```

Para pruebas locales con certificado propio también puede ejecutarse Uvicorn con:

```bash
python -m uvicorn src.serving.api:app --host 127.0.0.1 --port 8000 --ssl-keyfile ./certs/local.key --ssl-certfile ./certs/local.crt
```

En un despliegue detrás de proxy TLS, active:

```bash
set PORTOPS_SECURE_COOKIES=1
set PORTOPS_ENABLE_HSTS=1
```

En Linux/macOS:

```bash
export PORTOPS_SECURE_COOKIES=1
export PORTOPS_ENABLE_HSTS=1
```

## Guardrail JavaScript

No se permite `npm install` como flujo de proyecto. El repositorio declara:

- `packageManager: pnpm@9.12.3`
- `scripts/ensure_pnpm.js` como `preinstall`
- `pnpm-workspace.yaml`

Comando de validación frontend:

```bash
corepack enable
pnpm check
```

El comando solo valida sintaxis de JavaScript e i18n; no instala dependencias porque la interfaz v1.0.0 usa assets estáticos propios y CDN explícitos.

## Puerta de salida para publicar v1.0.0

Antes de publicar:

```bash
python -m pytest -q
python -m pytest tests/test_agents_customs_mcp.py::test_inference_engine_quantile_anticrossing tests/test_agents_customs_mcp.py::test_inference_engine_all_ports -q -W error
node --check src/serving/static/js/auth_flow.js
node --check src/serving/static/js/app.js
node --check src/serving/static/js/safe_markdown.js
node scripts/validate_i18n.js
```

La interfaz administrativa sigue protegida por IAM/MFA y cambio obligatorio de contraseña. El frontend no es autoridad de seguridad; toda decisión de sesión, rol, permiso y acceso operativo debe validarse en backend.

## Despliegue local productivo con HTTPS y acceso LAN

Este proyecto incluye un perfil Docker de prueba productiva local llamado `prod-tls`. Usa TLS real dentro de Uvicorn, escucha en `0.0.0.0` para permitir acceso desde la red local y mantiene cookies seguras, HSTS y certificados montados desde el host.

1. Genere una autoridad certificadora local y un certificado de servidor con SAN para `localhost`, `127.0.0.1`, `portops.local` y las IPs LAN detectadas del equipo:

   ```powershell
   python scripts/generate_local_tls.py
   ```

   Si necesita forzar una IP adicional, use:

   ```powershell
   $env:PORTOPS_TLS_EXTRA_IPS="192.168.50.84"
   python scripts/generate_local_tls.py
   ```

2. Levante el servicio HTTPS productivo local:

   ```powershell
   docker compose --profile prod-tls up --build -d portops-prod
   ```

3. Pruebe en el mismo equipo:

   ```text
   https://127.0.0.1:8443/app
   ```

4. Pruebe desde otra laptop conectada a la misma red usando la IP LAN que imprime el generador, por ejemplo:

   ```text
   https://192.168.50.84:8443/app
   ```

5. Para que el navegador de la otra laptop confíe en el certificado sin advertencias, copie e instale como entidad raíz confiable el archivo:

   ```text
   .local/tls/portops-local-ca.crt
   ```

6. Si Windows bloquea el acceso desde la LAN, ejecute PowerShell como administrador y habilite el puerto:

   ```powershell
   New-NetFirewallRule -DisplayName "Panama PortOps-AI HTTPS 8443" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8443
   ```

Este perfil está diseñado para pruebas reales en red local. No lo exponga directamente a Internet sin un proxy/ingress administrado, rotación formal de secretos y certificados emitidos por una CA pública o corporativa.
