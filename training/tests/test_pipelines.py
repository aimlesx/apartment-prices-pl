"""Testy jednostkowe węzłów: data_processing, feature_engineering, modeling."""

import numpy as np
import pandas as pd
from apartment_prices.pipelines.data_processing.nodes import deduplicate_and_clean
from apartment_prices.pipelines.feature_engineering.nodes import (
    BOOL_COLS,
    CATEGORICAL,
    POI_COLS,
    engineer_features,
)
from apartment_prices.pipelines.modeling.nodes import regression_metrics, split_data


def _synthetic_clean(n: int = 40) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    data = {
        "id": [f"id{i}" for i in range(n)],
        "city": rng.choice(["warszawa", "krakow", "gdansk"], n),
        "type": rng.choice(["blockOfFlats", "apartmentBuilding", None], n),
        "squareMeters": rng.uniform(25, 150, n),
        "rooms": rng.integers(1, 6, n),
        "floor": rng.integers(0, 10, n).astype(float),
        "floorCount": rng.integers(1, 12, n).astype(float),
        "buildYear": rng.integers(1950, 2024, n).astype(float),
        "latitude": rng.uniform(50, 54, n),
        "longitude": rng.uniform(14, 24, n),
        "centreDistance": rng.uniform(0, 15, n),
        "poiCount": rng.integers(0, 100, n),
        "ownership": rng.choice(["condominium", "cooperative"], n),
        "buildingMaterial": rng.choice(["brick", "concreteSlab", None], n),
        "condition": rng.choice(["premium", "low", None], n),
        "price": rng.integers(200_000, 2_000_000, n),
        "__month": "2024-06",
    }
    for col in POI_COLS:
        data[col] = rng.uniform(0, 2, n)
    for col in BOOL_COLS:
        data[col] = rng.choice(["yes", "no"], n)
    return pd.DataFrame(data)


def test_deduplicate_keep_last_and_filter():
    raw = pd.DataFrame(
        {
            "id": ["a", "a", "b", "c"],
            "__month": ["2024-01", "2024-02", "2024-01", "2024-01"],
            "ownership": ["condominium", "condominium", "cooperative", "udział"],
            "price": [300_000, 320_000, 500_000, 400_000],
        }
    )
    params = {
        "sale_ownership": ["condominium", "cooperative"],
        "price_min": 150_000,
        "price_max": 3_250_000,
    }
    out = deduplicate_and_clean(raw, params)
    assert len(out) == 2  # a (keep-last) + b; 'udział' odrzucony
    assert out.set_index("id").loc["a", "price"] == 320_000  # najnowszy miesiąc
    assert "udział" not in set(out["ownership"])


def test_engineer_features_contract():
    out = engineer_features(_synthetic_clean())
    assert "__month" not in out.columns
    assert {"id", "price"} <= set(out.columns)  # przechodzą do podziału
    for col in [
        "age",
        "floor_ratio",
        "rooms_per_m2",
        "amenity_score",
        "floor_is_missing",
    ]:
        assert col in out.columns
    for col in CATEGORICAL:
        assert str(out[col].dtype) == "category"
        assert "missing" in set(out[col].cat.categories) or out[col].notna().all()


def test_split_no_id_leak():
    model_input = engineer_features(_synthetic_clean(40))
    params = {
        "target": "price",
        "group_col": "id",
        "test_size": 0.25,
        "random_state": 42,
    }
    x_train, x_test, y_train, y_test = split_data(model_input, params)
    assert len(x_train) + len(x_test) == len(model_input)
    assert "id" not in x_train.columns
    assert "price" not in x_train.columns


def test_regression_metrics_perfect():
    y = np.array([200_000.0, 500_000.0, 1_000_000.0])
    m = regression_metrics(y, y)
    assert m["r2"] == 1.0
    assert m["rmse"] == 0.0
