FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./

RUN pip install --no-cache-dir uv 

RUN uv sync --frozen --no-dev

COPY rads_explorer ./rads_explorer

COPY html ./html

EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:9000/health || exit 1

CMD ["/app/.venv/bin/uvicorn", "rads_explorer.interfaces.main:app", "--host", "0.0.0.0", "--port", "9000"]
