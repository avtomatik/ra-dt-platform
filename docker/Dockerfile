ARG PYTHON_BASE_IMAGE=python:3.14-slim
FROM ${PYTHON_BASE_IMAGE}

ARG DEPLOY_CONTAINER_GID
ARG DEPLOY_CONTAINER_UID
ARG DEPLOY_CONTAINER_USER

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid "${DEPLOY_CONTAINER_GID}" "${DEPLOY_CONTAINER_USER}" \
    && useradd \
        --gid "${DEPLOY_CONTAINER_GID}" \
        --uid "${DEPLOY_CONTAINER_UID}" \
        --create-home \
        --shell /bin/bash \
        "${DEPLOY_CONTAINER_USER}"

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

COPY radp ./radp

COPY html ./html

COPY data ./data

RUN mkdir -p /app/data/exports

RUN chown -R "${DEPLOY_CONTAINER_UID}:${DEPLOY_CONTAINER_GID}" /app

USER ${DEPLOY_CONTAINER_USER}

EXPOSE 9000

HEALTHCHECK \
    --interval=30m \
    --timeout=10s \
    --start-period=30s \
    --retries=3 \
    CMD curl -fsS http://localhost:9000/health || exit 1

CMD [ "/app/.venv/bin/uvicorn", "radp.interfaces.api.main:app", "--host", "0.0.0.0", "--port", "9000" ]
