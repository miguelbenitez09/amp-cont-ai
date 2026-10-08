# Mejoras de interfaz — 8 de octubre de 2026

Se actualizó el diseño compartido del portal y las diez áreas operativas: navegación lateral en escritorio, menú desplegable en móvil, tipografía, tarjetas, formularios, tablas, gráficos y diálogos. La descripción extensa del proyecto se conserva en un bloque desplegable.

Se corrigieron los anchos fijos que recortaban paneles en móvil, el desbordamiento del portal, la compresión de la cabecera de configuración, y el cambio de tema que eliminaba las clases de interfaz y autenticación del documento. Configuración ahora se cierra con Escape conservando la confirmación de cambios pendientes.

## Verificación

- 43 pruebas existentes de interfaz, sesión y seguridad aprobadas.
- Prueba funcional en Chromium: 390×844, 768×1024 y 1440×900; idiomas español, inglés y portugués, validación aduanera y diálogo de sesión: aprobada.
- `scripts/verify_interface_design.py`: recorre las diez áreas y el portal en tres tamaños, verifica selección de navegación, paneles visibles, anchos de tarjetas, cambio de tema y cierre de configuración. Resultado detallado en `verification.json`; capturas en esta carpeta.

## Límites

Los estilos compartidos también están vinculados a las páginas del framework, pero sus rutas no se sirven como aplicación independiente en el servidor activo: se devuelve la aplicación operativa. Su ejecución independiente queda no verificada. No se declara conformidad completa WCAG 2.2 AA ni validación en Firefox/WebKit. Los formularios administrativos con sesión privilegiada no se han recorrido visualmente en esta revisión.
