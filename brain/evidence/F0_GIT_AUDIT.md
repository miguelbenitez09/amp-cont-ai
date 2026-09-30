# F0 — Auditoría de superficie pública (2026-09-29)

## Resultado

`BLOCKED_FOR_PUBLIC_RELEASE`.

El árbol rastreado contiene cuatro módulos bajo `src/data/scrapers/`, un inicializador y tests que mencionan scrapers. También contiene `data/raw/.gitkeep`, que es seguro como marcador vacío pero debe conservarse sin archivos derivados. No se encontraron CSV, XLSX, Parquet, claves o archivos `.env` rastreados en la inspección actual.

`.gitignore` y `.dockerignore` ya bloquean nuevos archivos privados, pero no eliminan archivos rastreados ni limpian el historial. La distribución pública requiere migrar los scrapers a almacenamiento privado y revisar historial, releases, artefactos e imágenes antes de declararse publicable.

## Decisiones

- No se reescribió el historial ni se borraron archivos en F0.
- El workflow de pruebas permanece ejecutable durante la migración.
- La gate de release público debe fallar mientras existan scrapers rastreados.
- La gate no debe confundir `src/infrastructure/secrets/` (código de gestión de secretos) con secretos almacenados.

## Evidencia

La lista se obtiene con `git ls-files` en el commit activo. Este informe no certifica que el historial remoto, forks o clones externos estén limpios.
