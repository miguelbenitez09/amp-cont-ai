# Tarjetas y temas — 8 de octubre de 2026

Las tarjetas operativas, estadísticas, administrativas, educativas y generadas por JavaScript comparten superficies, bordes y acentos derivados del tema activo. Los bloques de detalle y etiquetas ya no fijan cian o azul. Se conservan los colores semánticos de advertencia, éxito y error.

Las capacidades usan filas alineadas para títulos, descripciones, detalles y acciones, con etiquetas que pueden envolver texto. Se corrigió la fórmula de residuos que se mostraba como código LaTeX. En móvil las capacidades se organizan en una columna.

Se retiraron las variables de color fijas del rediseño anterior que anulaban las paletas. Los estilos de tarjetas del framework se cargan después de sus estilos dinámicos para mantener el contrato. Se corrigió también la legibilidad de texto secundario y navegación en el tema claro.

## Comprobaciones

- 130 comprobaciones de pantalla y tema: diez áreas operativas × seis temas × dos tamaños, más portal × cinco temas × dos tamaños. Sin diferencias de fondo respecto a la paleta ni tarjetas fuera de la pantalla en los casos comprobados. Incluyen bloques internos de capacidades.
- 90 comprobaciones visuales del framework: nueve rutas × cinco temas × dos tamaños. Sin fallos detectados. Ejecución en servidor estático aislado; los estados de acceso y error son los reales al carecer de API en ese servidor.
- 19 pruebas automatizadas aprobadas: 16 existentes y tres nuevas para asegurar cobertura de tipos de tarjeta, carga del estilo compartido y conservación de las variables de tema.
- Prueba funcional de la aplicación en 390×844, 768×1024 y 1440×900 aprobada: idiomas, validación aduanera, ausencia de desbordamiento y diálogo accesible de sesión.

Resultados: `verification.json`, `framework-verification.json`. Capturas por tema y tamaño en esta carpeta.

## Alcance de la evidencia

Chromium. No se declara certificación WCAG ni prueba funcional del backend del framework. Los formularios privilegiados y los estados generados que requieren operaciones o datos específicos reciben los estilos compartidos, pero no todos fueron abiertos visualmente con una sesión administrativa.
