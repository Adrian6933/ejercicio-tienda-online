FROM python:3.13-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY requirements.lock ./
RUN python -m venv /opt/venv && /opt/venv/bin/pip install -r requirements.lock

FROM python:3.13-slim AS runtime
ENV PATH=/opt/venv/bin:$PATH PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN groupadd --gid 10001 shop && useradd --uid 10001 --gid shop --create-home shop
COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
COPY --chown=shop:shop app ./app
COPY --chown=shop:shop alembic ./alembic
COPY --chown=shop:shop alembic.ini ./
COPY --chown=shop:shop data ./data
RUN mkdir -p logs && chown shop:shop logs
USER shop
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=30s CMD ["python","-c","import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["sh","-c","python -m app.manage migrate && python -m app.manage seed && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
