# Lekki obraz serwisu inferencyjnego. Kontekst budowania = korzeń repo
# (docker compose -f deploy/docker-compose.yml lub `make up`). Wymaga uv.lock.
#
# Model NIE jest wbudowany w obraz (D8) — montujemy go przy starcie (MODEL_URI=/app/model)
# (samodzielny artefakt MLflow z kodem cech przez code_paths; `make export-model`).

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Najpierw metadane workspace — lepszy cache warstw.
COPY pyproject.toml uv.lock ./
COPY training/pyproject.toml training/pyproject.toml
COPY serving/pyproject.toml serving/pyproject.toml

# Instaluj WYŁĄCZNIE zależności pakietu serving (bez bibliotek treningowych, bez Kedro).
RUN uv sync --package apartment-prices-serving --no-dev --frozen --no-install-workspace

FROM python:3.12-slim-bookworm AS runtime
# libgomp1 — biblioteka OpenMP wymagana w runtime przez LightGBM.
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY serving/apartment_serving /app/apartment_serving
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    MODEL_URI=/app/model
EXPOSE 8000
CMD ["uvicorn", "apartment_serving.main:app", "--host", "0.0.0.0", "--port", "8000"]
