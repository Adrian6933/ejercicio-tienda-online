# Tienda online

Proyecto de tienda con FastAPI, React/TypeScript y PostgreSQL. Incluye catálogo con filtros, imágenes y detalle, carrito, pedidos, registro y sesiones, direcciones versionadas, histórico de precios y pagos de prueba.

## Ejecutar con Docker

Requisitos: Docker Desktop con Compose.

```powershell
.\scripts\preparar.ps1
docker compose up --build -d
```

- Web: <http://localhost:15173>
- Documentación de la API: <http://localhost:18000/docs>
- Salud: <http://localhost:18000/health>
- PostgreSQL: `127.0.0.1:15432`, base y usuario `shop`; la contraseña se genera en `.env`.

La compra funciona en modo demo por defecto: registra una cuenta, guarda una dirección, añade productos y simula el pago. No hay cobros reales. Los productos y datos de prueba son ficticios.

Detener conservando datos: `docker compose stop`. No usar `down -v` si se quieren conservar los volúmenes.

## Desarrollo local

Python 3.13 y Node 22.

```powershell
.\scripts\setup-local.ps1
cd backend
..\.venv\Scripts\python.exe -m app.manage migrate
..\.venv\Scripts\python.exe -m app.manage seed
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

En otra terminal: `cd frontend` y `npm run dev`. La web nativa abre en <http://localhost:5173>. Sin `DATABASE_URL`, el backend usa SQLite.

## Pruebas

Desde `backend`: `..\.venv\Scripts\python.exe -m pytest`. Para comprobar concurrencia, usar una base PostgreSQL de pruebas mediante `TEST_DATABASE_URL`.

Desde `frontend`: `npm test` y `npm run build`. Para navegador: `npx playwright install chromium` y `npm run test:e2e`. Con Docker, definir `E2E_URL=http://localhost:15173`.

El código del pipeline está en `ci/github-actions.yml` como plantilla. La comprobación de configuración se ejecuta con `python scripts/validar_entrega.py`.

## Pagos y configuración

La integración de Stripe admite claves de prueba. Para usar su sandbox configurar `PAYMENT_MODE=stripe`, `STRIPE_SECRET_KEY` y `STRIPE_WEBHOOK_SECRET` en el entorno, además de un webhook a `/webhooks/stripe`. El código verifica firma, duplicados, importe y moneda. La confirmación del pago depende del evento del proveedor.

Nunca publicar `.env`, claves, bases de datos o logs de ejecución. `.env.example` contiene únicamente nombres y valores de ejemplo.

`render.yaml` es una configuración de despliegue; el repositorio no implica que haya un sitio externo desplegado.

## Herramientas

- `scripts/build.sh`: pruebas, compilación y paquete con SHA-256.
- `scripts/backup.py`: copia y restauración de la base de datos.
- `scripts/auditar.py`: comprobación de endpoints.
- `docker compose --profile observability up -d` y `scripts/configurar_kibana.py`: logs, panel y alerta locales. Kibana en `http://localhost:15601`.
- [Recuperación](docs/RECUPERACION.md) y [fuentes y créditos de imágenes](docs/FUENTES.md).
