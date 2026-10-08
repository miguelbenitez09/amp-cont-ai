# Transiciones de interfaz

La aplicación operativa sustituye las animaciones superpuestas por una entrada de 200 ms. Las vistas inactivas permanecen fuera del renderizado. Los diálogos animan su superficie interior sin desvanecer el fondo de protección. Configuración, autenticación y pasos de instalación comparten la presentación.

Los gráficos existentes se detienen, redimensionan y actualizan al volver al panel. Durante el recálculo se oculta el canvas anterior y el estado de carga usa una superficie opaca del tema actual.

El framework muestra un estado de carga al iniciar una navegación. Las respuestas de consultas de una generación anterior se descartan y no sustituyen la ruta actual. Los usuarios que prefieren movimiento reducido reciben cambios sin animación.

## Verificación

- 240 muestras de cuadros de animación entre las diez áreas, recorriendo ida y vuelta en 390 y 1440 px, con movimiento normal y reducido: sólo aparece el panel seleccionado.
- Respuesta de modelos deliberadamente retrasada mientras se navega a datasets: la vista final permanece en datasets.
- 17 pruebas existentes de interfaz, estado y contrato de tarjetas aprobadas.
- Pronóstico, simulación y recuperación de errores de la prueba funcional de navegación aprobados.

Resultados detallados en `verification.json`. La prueba de carrera del framework utiliza respuestas controladas en un servidor aislado. No implica validar todas sus operaciones administrativas o servicios externos.

La contraseña inicial del archivo local de instalación fue comparada con el hash de la cuenta root activa: coincide y requiere cambio en el primer acceso. No se incluyen credenciales en este informe.
