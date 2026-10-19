from pathlib import Path
from time import perf_counter
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from .config import Settings
from .database import make_engine, factory
from .observability import configure_logging
from .routes import catalog, accounts, commerce, payments


def create_app(settings=None):
    settings = settings or Settings()
    settings.validate()
    application = FastAPI(
        title="Taller · API de la tienda", version="1.0.0", description="Proyecto de tienda online. Catálogo, cuentas, pedidos y pagos de prueba."
    )
    application.state.settings = settings
    application.state.engine = make_engine(settings.database_url)
    application.state.sessions = factory(application.state.engine)
    log = configure_logging(settings.log_file)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    @application.middleware("http")
    async def trace(request: Request, call_next):
        trace_id = uuid4().hex
        start = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            log.exception("Petición fallida", extra={"event_action": "http.error", "trace_id": trace_id, "status_code": 500})
            raise
        response.headers["X-Request-ID"] = trace_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store" if request.url.path.startswith(("/me", "/auth", "/orders", "/carts")) else "no-cache"
        route = getattr(request.scope.get("route"), "path", "unmatched")
        if request.url.path not in {"/health", "/metrics"}:
            # Plantilla de la ruta, nunca cookies, email, dirección ni token del carrito.
            level = log.warning if response.status_code >= 400 else log.info
            level(
                "Petición completada",
                extra={
                    "event_action": "http.request",
                    "trace_id": trace_id,
                    "route": route,
                    "status_code": response.status_code,
                    "duration_ms": round((perf_counter() - start) * 1000, 3),
                },
            )
        return response

    @application.get("/health", tags=["Operación"])
    def health():
        with application.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "version": settings.version, "payment_mode": settings.payment_mode}

    @application.get("/version", tags=["Operación"])
    def version():
        return {"version": settings.version}

    for router in (catalog.router, accounts.router, commerce.router, payments.router):
        application.include_router(router)
        application.include_router(router, prefix="/v1", include_in_schema=False)
    application.mount("/images", StaticFiles(directory=Path(__file__).resolve().parents[1] / "data" / "images", check_dir=False), name="images")
    return application


app = create_app()
