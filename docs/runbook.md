# Runbook — uruchamianie i obsługa

Wszystkie skróty z `Makefile` uruchamiaj z korzenia repo (`project/`).

## 0. Wymagania wstępne

- Python 3.12, [uv](https://docs.astral.sh/uv/)
- **libomp** (LightGBM): macOS `brew install libomp`; Debian/Ubuntu `apt-get install libgomp1`
- (opcjonalnie) Docker + `docker compose`

## 1. Środowisko i dane

```bash
make install          # uv sync --all-packages (cały workspace, z locka)
make data             # rozpakuj archive.zip (z Kaggle) -> training/data/01_raw/
```

Dane są **poza gitem**; pobierz dataset z Kaggle i umieść `archive.zip` w korzeniu repo.

## 2. Trening

```bash
make pipeline         # baseline Kedro: data_processing -> feature_engineering -> modeling
                      # wynik: training/data/08_reporting/metrics.json (R² baseline ~0.8917)

cd training && DO_NOT_TRACK=1 uv run kedro run --pipeline optimization
                      # porównanie 3 rodzin + Optuna + rejestracja championa w MLflow
                      # wynik: leaderboard.json, tuning_result.json, optimized_metrics.json
```

`make viz` — graf pipeline'u Kedro (http://localhost:4141).

## 3. MLflow UI (eksperymenty, leaderboard, Optuna, Registry)

```bash
make mlflow-ui        # http://localhost:5000  (backend sqlite: training/mlflow.db)
```

## 4. Serwowanie lokalnie

```bash
make serve            # FastAPI na http://localhost:8000 (model z lokalnego rejestru @production)
```

Predykcja:

```bash
curl -s -X POST http://localhost:8000/predict -H 'Content-Type: application/json' -d '{
  "city":"warszawa","squareMeters":60,"rooms":3,"latitude":52.23,"longitude":21.01,
  "centreDistance":3.5,"ownership":"condominium","hasParkingSpace":true,"hasBalcony":true,
  "hasSecurity":false,"hasStorageRoom":true}'
# -> {"price_pln": ...}
```

Pola **wymagane** (11): `city, squareMeters, rooms, latitude, longitude, centreDistance,
ownership, hasParkingSpace, hasBalcony, hasSecurity, hasStorageRoom`. Pozostałe 15 są
opcjonalne. Dokumentacja interaktywna: `http://localhost:8000/docs`.

## 5. Pełny stack w Dockerze (API + Prometheus + Grafana)

```bash
make up               # 1) export-model -> deploy/model, 2) docker compose up --build
```

| Usługa | URL | Uwagi |
|--------|-----|-------|
| API | http://localhost:8000 | `/predict`, `/health`, `/metrics` |
| Prometheus | http://localhost:9090 | scrape `api:8000/metrics` |
| Grafana | http://localhost:3000 | login `admin` / `admin`, dashboard provisioned |

`make down` — zatrzymaj i usuń stack.

## 6. Jakość

```bash
make lint             # ruff: lint + sprawdzenie formatu
make test             # pytest (training + serving)
```

## 7. CI/CD (GitHub Actions)

| Workflow | Wyzwalacz | Sekrety |
|----------|-----------|---------|
| `ci.yml` | PR / push | — |
| `cd.yml` | push `main` / tag `v*` | `GITHUB_TOKEN` (automatyczny) |
| `continuous-training.yml` | cron (pn 03:00 UTC) / ręcznie | `KAGGLE_USERNAME`, `KAGGLE_KEY`, opc. `MLFLOW_TRACKING_URI` |

## 8. Najczęstsze problemy

- **`OSError: libomp.dylib`** (macOS) — `brew install libomp`.
- **`kedro: No such command 'run'`** — uruchamiaj z `training/` (`cd training && uv run kedro run`).
- **Port 8000 zajęty** — zmień mapowanie portu lub zatrzymaj kolidujący proces.
- **`/metrics` puste** — wykonaj najpierw `/predict` (metryki rosną przy obsłudze żądań).
