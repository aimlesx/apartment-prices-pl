"""Węzły pipeline'u modeling: podział grupowy, trening LightGBM i ewaluacja.

Podział jest **grupowy po ``id``** (``GroupShuffleSplit``) - gwarantuje, że żadne
mieszkanie nie trafi jednocześnie do treningu i testu (kontrola wycieku tożsamości).
Target to ``log1p(price)``; wszystkie metryki liczone są w PLN po ``expm1``.
"""

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import GroupShuffleSplit


def regression_metrics(y_true_pln: np.ndarray, y_pred_pln: np.ndarray) -> dict:
    """Metryki regresji w PLN (RMSE, MAE, MAPE %, R²)."""
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true_pln, y_pred_pln))),
        "mae": float(mean_absolute_error(y_true_pln, y_pred_pln)),
        "mape_pct": float(mean_absolute_percentage_error(y_true_pln, y_pred_pln) * 100),
        "r2": float(r2_score(y_true_pln, y_pred_pln)),
    }


def split_data(model_input: pd.DataFrame, params: dict):
    """Podział grupowy po ``id`` na zbiór treningowy i testowy (target ``log1p``)."""
    target, group = params["target"], params["group_col"]
    y = np.log1p(model_input[target])
    X = model_input.drop(columns=[target, group])
    groups = model_input[group]

    splitter = GroupShuffleSplit(
        n_splits=1, test_size=params["test_size"], random_state=params["random_state"]
    )
    train_idx, test_idx = next(splitter.split(X, y, groups))

    if set(groups.iloc[train_idx]) & set(groups.iloc[test_idx]):
        raise ValueError("Wyciek: wspólne id między train a test")

    return X.iloc[train_idx], X.iloc[test_idx], y.iloc[train_idx], y.iloc[test_idx]


def train_model(
    X_train: pd.DataFrame, y_train: pd.Series, params: dict
) -> LGBMRegressor:
    """Trenuj LightGBM; kolumny ``category`` traktowane natywnie jako kategoryczne."""
    categorical = X_train.select_dtypes("category").columns.tolist()
    model = LGBMRegressor(**params["lgbm"])
    model.fit(X_train, y_train, categorical_feature=categorical)
    return model


def evaluate_model(
    model: LGBMRegressor, X_test: pd.DataFrame, y_test: pd.Series
) -> dict:
    """Policz metryki regresji w PLN na zbiorze testowym."""
    y_pred_pln = np.expm1(model.predict(X_test))
    y_true_pln = np.expm1(y_test.to_numpy())
    return regression_metrics(y_true_pln, y_pred_pln)
