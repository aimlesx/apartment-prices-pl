.PHONY: install lock data lint format test pipeline viz serve up down

install:           ## zsynchronizuj środowisko całego workspace
	uv sync --all-packages

lock:              ## wygeneruj/odśwież uv.lock
	uv lock

data:              ## rozpakuj archive.zip (z Kaggle) do training/data/01_raw/
	unzip -o archive.zip -d training/data/01_raw/

lint:              ## ruff: lint + sprawdzenie formatu
	uv run ruff check .
	uv run ruff format --check .

format:            ## ruff: auto-format
	uv run ruff format .

test:              ## testy (training + serving)
	uv run pytest

pipeline:          ## uruchom cały pipeline Kedro
	cd training && DO_NOT_TRACK=1 uv run kedro run

viz:               ## wizualizacja grafu pipeline'u
	cd training && DO_NOT_TRACK=1 uv run kedro viz

serve:             ## lokalny serwis inferencyjny FastAPI
	uv run --package apartment-prices-serving uvicorn apartment_serving.main:app --reload

up:                ## cały stack w Dockerze (API + MLflow + Prometheus + Grafana)
	docker compose -f deploy/docker-compose.yml up --build

down:
	docker compose -f deploy/docker-compose.yml down
