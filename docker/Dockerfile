FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY config ./config

RUN uv sync --frozen --no-dev

ENV PYTHONUNBUFFERED=1
ENV MTES_CONFIG_PATH=/app/config/config.example.yaml

ENTRYPOINT ["uv", "run", "python", "-m", "mtes.docker_stub"]
