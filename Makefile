.PHONY: install lock data lint format test pipeline optimize viz serve export-model mlflow-ui up down ui

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

pipeline:          ## pipeline Kedro: baseline (BEZ rejestracji championa)
	cd training && DO_NOT_TRACK=1 uv run kedro run

optimize:          ## porównanie modeli + Optuna + rejestracja championa (@production)
	cd training && DO_NOT_TRACK=1 uv run kedro run --pipeline optimization

viz:               ## wizualizacja grafu pipeline'u
	cd training && DO_NOT_TRACK=1 uv run kedro viz

serve:             ## lokalny serwis inferencyjny FastAPI (model z lokalnego rejestru MLflow)
	MLFLOW_TRACKING_URI=sqlite:///$(CURDIR)/training/mlflow.db \
		uv run uvicorn apartment_serving.main:app --host 0.0.0.0 --port 8000 --reload

export-model:      ## wyeksportuj model @production z rejestru do deploy/model/ (mount dla Dockera)
	rm -rf deploy/model
	MLFLOW_TRACKING_URI=sqlite:///$(CURDIR)/training/mlflow.db \
		uv run python -c "import mlflow; mlflow.artifacts.download_artifacts('models:/apartment-price-model@production', dst_path='deploy/model')"

mlflow-ui:         ## lokalny MLflow UI (eksperymenty, leaderboard, Optuna) na :5000
	cd training && uv run mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000

up: export-model   ## stack w Dockerze (API + Prometheus + Grafana); najpierw eksport modelu
	docker compose -f deploy/docker-compose.yml up --build

down:
	docker compose -f deploy/docker-compose.yml down -v

ui:                ## frontend demo (Vite + React) na :5173 — proxy /predict do API (API_TARGET, dom. :8000)
	cd web && npm install && npm run dev
