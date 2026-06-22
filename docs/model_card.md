# Model card — apartment-price-model

## Przeznaczenie

Przewidywanie **ceny sprzedaży mieszkania w Polsce** (PLN) na podstawie cech ogłoszenia
(lokalizacja, metraż, liczba pokoi, piętro, rok budowy, odległości do POI, udogodnienia).
Problem: **regresja**.

- **Zamierzone użycie:** szacowanie/wstępna wycena, analiza rynku, demo MLOps.
- **Poza zakresem:** wiążąca wycena, kredytowanie, mieszkania spoza zakresu danych (poniżej).

## Dane

[Apartment Prices in Poland](https://www.kaggle.com/datasets/krzysztofjamroz/apartment-prices-in-poland)
(Kaggle, `krzysztofjamroz`). 11 miesięcznych plików sprzedaży (2023-08 … 2024-06),
195 568 wierszy → po **deduplikacji keep-last po `id`** ~92 960 mieszkań z **15 miast**.

- **Target:** `price` (PLN), zakres **150 000 – 3 250 000** (dane wstępnie przycięte).
- **Wejście modelu:** 26 surowych cech; pochodne liczy `engineer_features`
  (np. `age`, `floor_ratio`, agregaty POI, flagi `*_is_missing`).
- **Transformacja targetu:** `log1p(price)` (skośność 1,76 → 0,07), metryki w PLN po `expm1`.

## Walidacja

- **Split główny:** `GroupShuffleSplit(test_size=0.2, seed=42)` **grupowany po `id`** —
  żadne mieszkanie nie trafia jednocześnie do train i test (kontrola wycieku tożsamości;
  losowy split przecieka 66,6% id i zawyża R²).
- **HPO:** Optuna (TPE, MedianPruner, 50 prób) optymalizowana na **5-fold `GroupKFold`**;
  holdout używany tylko raz, na końcu.

## Wyniki (grouped holdout, w PLN)

| Model | R² | RMSE | MAE | MAPE |
|-------|----|------|-----|------|
| Dummy (mediana) | ~0 | ~390k | — | — |
| Baseline LightGBM (domyślny) | 0,8917 | 129 859 | 85 288 | 10,87% |
| **Champion (LightGBM + Optuna)** | **0,9154** | **114 740** | **73 156** | **9,51%** |

Leaderboard porównania (CV-RMSE, PLN): LightGBM **132 492** < HistGBR 141 999 < Ridge 190 119.

> **Czerwona flaga:** R² > 0,93 traktujemy podejrzliwie (możliwy powrót wycieku — `id`,
> `__month` lub cena/m² jako cecha). Champion (0,9154) jest poniżej tego progu.

## Architektura modelu (artefakt)

`sklearn.Pipeline`:
1. `FunctionTransformer(engineer_features)` — surowe cechy → 26+ cech (kategorie natywne LGBM, NaN natywny),
2. `TransformedTargetRegressor(LGBMRegressor, func=log1p, inverse_func=expm1)`.

Zarejestrowany w MLflow jako `apartment-price-model`, alias **`@production`**, z sygnaturą,
`input_example` i kodem cech (`code_paths`). Serwis dostaje surowe cechy, otrzymuje PLN.

## Najlepsze hiperparametry (Optuna)

`learning_rate≈0.17 · num_leaves=86 · max_depth=6 · min_child_samples=40 ·
subsample≈0.81 · colsample_bytree≈0.72 · reg_alpha≈0.77 · reg_lambda≈0.44 ·
n_estimators≈1745` (dobrane z early stopping).

## Ograniczenia i ryzyka

- **Zakres stosowalności:** 15 dużych miast PL, okres 2023-08…2024-06, cena 150k–3,25M PLN.
  Poza tym zakresem model jest **nieważny**.
- **Drift:** rynek się zmienia; monitoring metrażu/cen (Prometheus/Grafana) + Continuous
  Training mają wychwytywać degradację.
- **Braki danych:** `condition` 74,8% i `buildingMaterial` 39,6% braków — niosą głównie
  sygnał „brak"; predykcje dla nietypowych kombinacji są mniej pewne.
- **Reprezentacja:** dane zdominowane przez duże miasta (zwł. Warszawę) — gorsza
  generalizacja na mniejsze rynki. Raport błędu w rozbiciu na miasto jest zalecany.
