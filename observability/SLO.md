# Objetivos de la práctica

- Disponibilidad: al menos 99 % de peticiones de aplicación sin respuesta 5xx en una ventana de 30 días.
- Latencia: p95 inferior a 500 ms para lecturas del catálogo, medido en servidor.
- Pagos: observar intentos fallidos y pedidos pendientes; los fallos de tarjeta no se confunden con indisponibilidad del backend.

Son objetivos propuestos para aprender a medir, no garantías de servicio. El panel usa `event.duration_ms`, `http.response.status_code` y `http.route`. No se registran correos, direcciones, cookies ni cuerpos de peticiones.

Alerta local: al menos 3 respuestas con status >= 400 en el último minuto. Provocar con `/productos` y dejar de hacerlo para ver la recuperación. Los 404 cuentan en esta alerta didáctica; en una operación real conviene separar 4xx y 5xx.
