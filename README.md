# Predykcja cen mieszkań w Polsce

Projekt ML rozwiązujący problem **regresji** — przewidywanie ceny mieszkania (PLN)
na podstawie danych z portali ogłoszeniowych.

- **Dane:** [Apartment Prices in Poland](https://www.kaggle.com/datasets/krzysztofjamroz/apartment-prices-in-poland) (Kaggle)
- **Problem:** regresja (`price` w PLN); ~93 tys. mieszkań z 15 miast, 11 miesięcy (2023-08…2024-06).

## Architektura

Monorepo jako **workspace uv** (Python 3.12) z dwoma pakietami:

| Pakiet | Rola | Stack |
|--------|------|-------|
| `training/` | pozyskanie danych, inżynieria cech, modelowanie, HPO | Kedro, scikit-learn, LightGBM, Optuna, MLflow |
| `serving/` | serwis inferencyjny | FastAPI, Uvicorn, Prometheus (lekki klient MLflow) |

Wytrenowany model trafia do **MLflow Model Registry**; serwis ładuje go po URI.
Monitoring: Prometheus + Grafana. Jakość i dostarczanie: ruff, pytest, GitHub Actions (CI/CD).

## Wymagania

- Python 3.12, [uv](https://docs.astral.sh/uv/)
- (opcjonalnie) Docker + `docker compose` — pełny stack serwowania i monitoringu

## Dane

Pobierz dataset z Kaggle, umieść `archive.zip` w katalogu repozytorium i rozpakuj:

```bash
make data        # unzip archive.zip -> training/data/01_raw/
```

Dane (`training/data/**`) są **poza gitem** — wersjonujemy tylko strukturę katalogów.

## Szybki start

```bash
make install     # środowisko całego workspace (uv sync --all-packages)
make data        # rozpakuj dane do training/data/01_raw/
make pipeline    # pipeline Kedro (trening)
make test        # pytest
make lint        # ruff (lint + sprawdzenie formatu)
make viz         # graf pipeline'u Kedro (http://localhost:4141)
```

Pełny stack (API + MLflow + Prometheus + Grafana) — po etapie serwowania: `make up`.

## Struktura

```
training/    pakiet Kedro (apartment_prices): conf, data (8 warstw), pipelines, tests
serving/     serwis FastAPI (apartment_serving)
deploy/      docker-compose (stack serwowania)
monitoring/  konfiguracja Prometheus/Grafana
.github/     CI/CD (GitHub Actions)
```
