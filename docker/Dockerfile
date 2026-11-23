ARG DEPLOY_PYTHON_BASE_IMAGE=python:3.14-slim
FROM ${DEPLOY_PYTHON_BASE_IMAGE}

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        gosu \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-dev --no-install-project

COPY data ./data
COPY html ./html
COPY radp ./radp

RUN uv sync --locked --no-dev --no-editable

RUN mkdir -p /app/data/exports /app/logs

COPY docker/entrypoint.sh /usr/local/bin/radp-entrypoint

RUN chmod 0755 /usr/local/bin/radp-entrypoint

EXPOSE 9000

HEALTHCHECK --interval=30m --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:9000/health || exit 1

ENTRYPOINT ["/usr/local/bin/radp-entrypoint"]

CMD ["/app/.venv/bin/uvicorn", "radp.interfaces.api.main:app", "--host", "0.0.0.0", "--port", "9000"]
