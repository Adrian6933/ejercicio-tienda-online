# Recuperación y despliegue

1. Antes de cambiar el esquema, ejecutar `python scripts/backup.py` y conservar el fichero en un lugar privado. Probar periódicamente la restauración en otra BD vacía, nunca sobre la única copia.
2. Guardar la revisión Git y la revisión Alembic de la versión que funciona. El pipeline conserva el artefacto y su SHA-256.
3. Si falla una versión de aplicación y el esquema es compatible, desplegar la revisión anterior. Si el esquema cambió, valorar la compatibilidad; un downgrade destructivo no sustituye al backup.
4. Verificar `/health`, catálogo y flujo de pedido en un entorno de pruebas. Revisar errores y latencia en Kibana.
5. Comunicar el incidente al responsable del proyecto y documentar causa, corrección y test de regresión.

`render.yaml` es infraestructura preparada, no un despliegue realizado. Selecciona los planes gratuitos disponibles en la documentación consultada; revisar límites y condiciones de la cuenta antes de crear el Blueprint. Región común: Frankfurt. Completar las URLs HTTPS exactas, sin puertos locales. GitHub necesita autorización válida y Render necesita acceso al repositorio. No se han contratado servicios ni generado cargos.

Datos de QA y staging: usar los datos ficticios de seed y correos de `.test`. No copiar datos personales de producción sin anonimización. Usar Stripe sandbox en ambos entornos.
