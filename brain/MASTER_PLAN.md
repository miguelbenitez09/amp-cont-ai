# AMP-CONT-AI — Plan de implementación activo

## Producto objetivo

AMP-CONT-AI será un framework panameño instalable para ejecutar modelos entrenados con datos oficiales aprobados. La distribución pública contiene software, documentación, pesos publicados y datasets Bronce 2.0 aprobados. La adquisición privada contiene los conectores específicos, credenciales y Bronce original.

## LOOP ENGINEERING

Cada cambio sigue: observar evidencia → formular hipótesis → implementar un cambio reversible → verificar → registrar aprendizaje → integrar. Una tarea no se cierra por contar archivos, por una respuesta HTTP 200 o por una métrica escrita manualmente.

## Fases

| Fase | Estado | Salida |
|---|---|---|
| F0 Auditoría y protección | IN_PROGRESS | inventario, exposición Git, límites de distribución |
| F1 Privacidad y Bronce 2.0 | PLANNED | contratos, transformaciones y gates de publicación |
| F2 Framework público instalable | PLANNED | instalación, landing, catálogo e inferencia local |
| F3 Adquisición privada | PLANNED | conectores fuera del repositorio público y manifests |
| F4 Dataset/modelos públicos | PLANNED | releases versionadas con cards y checksums |
| F5 Interfaces y MLOps | PLANNED | control plane, ajustes, evaluación y observabilidad |
| F6 Reconstrucción | PLANNED | instalación limpia, pruebas E2E, backup y rollback |

## Regla de seguridad

Nunca se copiarán scrapers privados, RAW restringido, correspondencias de anonimización o secretos al repositorio público, imágenes, paquetes o artefactos de CI.
