# Navegación y recuperación de solicitudes

## Cambios

- Barra lateral de 224 px, versión contraída de 72 px y botón con el icono solicitado. Preferencia persistente y atajo Ctrl+Shift+S; en móvil el atajo abre/cierra el menú. Botones con nombres accesibles y títulos, iconos de 20 px y texto de 13 px.
- Una sesión inválida elimina su cookie al consultar `/api/v1/auth/me`. Las solicitudes de escritura recuperan el token CSRF si falta; una respuesta explícita del middleware de protección permite refrescar la sesión y reintentar una sola vez. No se reintentan operaciones que hayan llegado al controlador ni se desactiva la protección.
- Simulación: impide ejecuciones simultáneas, tiene límite de espera, valida resultados y muestra estado persistente de carga, éxito o error con recuperación. No presenta datos incompletos como un resultado válido.
- El motor no inicializado conserva HTTP 503, en lugar de convertirse en 500.
- La navegación pública no solicita el inventario administrativo de usuarios.

## Evidencia

29 pruebas de seguridad y sesión aprobadas, incluida recuperación de un token CSRF desactualizado en navegador autenticado, limpieza de cookie inválida y HTTP 503 del motor. Las 14 pruebas de interfaz/estado existentes también pasaron.

Prueba real en Chromium en móvil (390 px) y escritorio (1440 px): recorre diez áreas, contrae/restaura la barra, comprueba persistencia y atajo, comienza con una cookie inválida, provoca un fallo temporal 503 controlado, reintenta la simulación contra el servidor real y verifica gráfico y registro WORM. También ejecuta pronósticos reales. Sin errores JavaScript. Los HTTP 401 y 503 del informe son los fallos deliberadamente provocados para comprobar recuperación.

Prueba funcional existente en 390, 768 y 1440 px aprobada: idiomas, calculadora aduanera, validación de contenedor y acceso por teclado al diálogo de sesión.

## Límites

No se declara que toda la plataforma sea 100 % funcional: faltan recorridos completos con todas las combinaciones de permisos, servicios externos y estados de datos. Esta revisión verifica los flujos descritos; las integraciones que requieren credenciales o servicios externos siguen sin comprobación completa.
