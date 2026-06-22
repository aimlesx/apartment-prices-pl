# Predykcja cen mieszkań w Polsce 🏙️

Projekt ML (problem **regresji**) przewidujący cenę mieszkania w PLN — od baseline'u w
Jupyterze, przez pipeline Kedro, MLflow + strojenie Optuną, po serwis FastAPI z monitoringiem
i CI/CD. Zbudowany jako **monorepo MLOps**.

- **Dane:** [Apartment Prices in Poland](https://www.kaggle.com/datasets/krzysztofjamroz/apartment-prices-in-poland) (Kaggle)
- **Problem:** regresja (`price` w PLN); ~93 tys. mieszkań z 15 miast, 11 miesięcy (2023-08…2024-06)
- **Dokumentacja:** [architektura](docs/architecture.md) · [model card](docs/model_card.md) · [runbook](docs/runbook.md)

## Wynik

Champion (LightGBM po strojeniu Optuną) na **grupowym** holdoutcie (split po `id`, w PLN):

| Model | R² | RMSE | MAE | MAPE |
|-------|----|------|-----|------|
| Baseline LightGBM | 0,8917 | 129 859 | 85 288 | 10,87% |
| **Champion (Optuna)** | **0,9154** | **114 740** | **73 156** | **9,51%** |

## Architektura

![Architektura MLOps](docs/diagrams/architecture.svg)

Monorepo jako **workspace uv** (Python 3.12) z dwoma pakietami:

| Pakiet | Rola | Stack |
|--------|------|-------|
| `training/` | pozyskanie danych, inżynieria cech, modelowanie, HPO | Kedro, scikit-learn, LightGBM, Optuna, MLflow |
| `serving/` | serwis inferencyjny | FastAPI, Uvicorn, Prometheus, mlflow-skinny |

Model trafia do **MLflow Model Registry** (`apartment-price-model @production`) jako kompletny
`Pipeline(inżynieria cech + LightGBM)` — serwis przyjmuje surowe cechy i zwraca cenę, bez
rozjazdu cech między treningiem a serwowaniem. Szczegóły: [docs/architecture.md](docs/architecture.md).

## Wymagania

- Python 3.12, [uv](https://docs.astral.sh/uv/)
- **libomp** (LightGBM): macOS `brew install libomp`, Debian/Ubuntu `apt-get install libgomp1`
- (opcjonalnie) Docker + `docker compose` — pełny stack serwowania i monitoringu

## Szybki start

```bash
make install     # środowisko całego workspace (uv sync --all-packages)
make data        # rozpakuj archive.zip (z Kaggle) -> training/data/01_raw/
make pipeline    # pipeline Kedro: trening baseline
make serve       # serwis FastAPI na http://localhost:8000 (model z rejestru @production)
make up          # pełny stack w Dockerze (API + Prometheus + Grafana)
```

Pełne strojenie + rejestracja championa:
`cd training && DO_NOT_TRACK=1 uv run kedro run --pipeline optimization`.
Więcej poleceń (MLflow UI, eksport modelu, monitoring): [docs/runbook.md](docs/runbook.md)
oraz `make help`-owe komentarze w [Makefile](Makefile).

Dane (`training/data/**`) są **poza gitem** — wersjonujemy tylko strukturę katalogów.

## Etapy (mapa na repozytorium)

| Etap | Zakres | Gdzie |
|------|--------|-------|
| 1 | Organizacja, środowisko, CI | `pyproject.toml`, `uv.lock`, `.github/workflows/ci.yml` |
| 2 | Baseline (EDA + model) | [`notebooks/01_baseline.ipynb`](notebooks/01_baseline.ipynb) |
| 3 | Pipeline Kedro | `training/src/apartment_prices/pipelines/` |
| 4 | MLflow + porównanie + Optuna + Registry | pipeline `optimization` |
| 5 | API + Docker + monitoring | `serving/`, `deploy/`, `monitoring/` |
| 6 | MLOps: CD + Continuous Training | `.github/workflows/{cd,continuous-training}.yml` |
| 7 | Dokumentacja + diagram | `docs/`, `README.md` |

## Struktura

```
training/    pakiet Kedro (apartment_prices): conf, data (8 warstw), pipelines, tests
serving/     serwis FastAPI (apartment_serving): schemas, model, main, Dockerfile
deploy/      docker-compose (API + Prometheus + Grafana)
monitoring/  Prometheus + Grafana (provisioning: datasource + dashboard)
docs/        architektura, model card, runbook, diagram
scripts/     narzędzia (kontrola jakości Continuous Training)
.github/     CI/CD (GitHub Actions)
```

## Jakość

`ruff` (lint + format), `pytest` (testy węzłów Kedro i API), `pre-commit`, CI na każdym PR.
```bash
make lint && make test
```
