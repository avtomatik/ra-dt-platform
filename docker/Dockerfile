FROM python:3.14-slim

ARG RADP_CONTAINER_USER
ARG RADP_CONTAINER_UID
ARG RADP_CONTAINER_GID

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid "${RADP_CONTAINER_GID}" "${RADP_CONTAINER_USER}" \
    && useradd \
        --uid "${RADP_CONTAINER_UID}" \
        --gid "${RADP_CONTAINER_GID}" \
        --create-home \
        --shell /bin/bash \
        "${RADP_CONTAINER_USER}"

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

COPY radp ./radp

COPY html ./html

COPY data ./data

RUN mkdir -p /app/data/exports

RUN chown -R "${RADP_CONTAINER_UID}:${RADP_CONTAINER_GID}" /app

USER ${RADP_CONTAINER_USER}

EXPOSE 9000

HEALTHCHECK \
    --interval=30m \
    --timeout=10s \
    --start-period=30s \
    --retries=3 \
    CMD curl -fsS http://localhost:9000/health || exit 1

CMD [ "/app/.venv/bin/uvicorn", "radp.interfaces.api.main:app", "--host", "0.0.0.0", "--port", "9000" ]
