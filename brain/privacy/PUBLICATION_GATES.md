# Gates de publicación

Un dataset o modelo solo se publica cuando:

1. Tiene licencia/permiso documentado.
2. No contiene secretos, sesiones, rutas privadas o scrapers.
3. Pasa el escaneo de datos sensibles y revisión de reidentificación.
4. Tiene manifest, checksum SHA-256, versión y procedencia.
5. El modelo tiene evaluación reproducible, card, limitaciones y base de datos publicada declarada.
6. La allowlist de release y el workflow público lo aceptan.

Un resultado `UNKNOWN`, `BLOCKED` o `SKIP` impide la publicación.
