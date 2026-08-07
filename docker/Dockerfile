FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

COPY radp ./radp

COPY html ./html

COPY data ./data

RUN mkdir -p /app/data/exports

EXPOSE 9000

HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=15s \
    --retries=3 \
    CMD curl -fsS http://localhost:9000/health || exit 1

CMD [ "/app/.venv/bin/uvicorn", "radp.interfaces.api.main:app", "--host", "0.0.0.0", "--port", "9000" ]
