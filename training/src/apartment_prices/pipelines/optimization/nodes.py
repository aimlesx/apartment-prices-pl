"""Węzły pipeline'u optimization (etap 4).

Trzy kroki, wszystkie logowane do MLflow (lokalny backend SQLite - wspiera Registry):
1. ``compare_model_families`` - >=3 rodziny modeli na 5-fold ``GroupKFold`` -> leaderboard.
2. ``tune_lightgbm`` - Optuna (TPE, MedianPruner) stroi LightGBM na tej samej CV.
3. ``register_champion`` - champion jako ``Pipeline(FE + TransformedTargetRegressor(LGBM))``
   trenowany na SUROWYCH cechach (te same co w serwisie), zarejestrowany w Model Registry
   wraz z sygnaturą, ``input_example`` i kodem cech (``code_paths``).
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor, early_stopping, log_evaluation
from sklearn.base import clone
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    FunctionTransformer,
    OneHotEncoder,
    OrdinalEncoder,
    StandardScaler,
)

from apartment_prices.features import CATEGORICAL, engineer_features
from apartment_prices.pipelines.modeling.nodes import regression_metrics

EXPERIMENT = "apartment-prices"
REGISTERED_MODEL = "apartment-price-model"
MIN_PRODUCTION_R2 = 0.89  # champion musi co najmniej dorównać baseline (~0.8917)


def _setup_mlflow():
    import mlflow

    # Czytaj URI ze środowiska - pozwala Continuous Training rejestrować na ZDALNYM
    # rejestrze (MLFLOW_TRACKING_URI), a lokalnie domyśla się backendu SQLite.
    uri = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    mlflow.set_tracking_uri(uri)
    mlflow.set_registry_uri(os.getenv("MLFLOW_REGISTRY_URI", uri))
    mlflow.set_experiment(EXPERIMENT)
    return mlflow


def _run(mlflow, name: str):
    """Start runu MLflow - zagnieżdżony, jeśli kedro-mlflow otworzył już rodzica."""
    return mlflow.start_run(run_name=name, nested=mlflow.active_run() is not None)


def _split_indices(model_input: pd.DataFrame, split: dict):
    splitter = GroupShuffleSplit(
        n_splits=1, test_size=split["test_size"], random_state=split["random_state"]
    )
    return next(splitter.split(model_input, groups=model_input[split["group_col"]]))


def _train_view(model_input: pd.DataFrame, split: dict):
    """Zwróć część TRENINGOWĄ: X (cechy), y (log target), groups (id)."""
    train_idx, _ = _split_indices(model_input, split)
    train = model_input.iloc[train_idx]
    y_log = np.log1p(train[split["target"]]).reset_index(drop=True)
    groups = train[split["group_col"]].reset_index(drop=True)
    X = train.drop(columns=[split["target"], split["group_col"]]).reset_index(drop=True)
    return X, y_log, groups


def _cv_rmse_pln(estimator, X, y_log, groups, n_splits, categorical=None) -> tuple:
    """Średnie i odchylenie RMSE w PLN z ``GroupKFold`` (predykcje po ``expm1``)."""
    gkf = GroupKFold(n_splits=n_splits)
    scores = []
    for tr, va in gkf.split(X, y_log, groups):
        est = clone(estimator)
        if categorical is not None:
            est.fit(X.iloc[tr], y_log.iloc[tr], categorical_feature=categorical)
        else:
            est.fit(X.iloc[tr], y_log.iloc[tr])
        pred = np.expm1(est.predict(X.iloc[va]))
        true = np.expm1(y_log.iloc[va].to_numpy())
        scores.append(np.sqrt(mean_squared_error(true, pred)))
    return float(np.mean(scores)), float(np.std(scores))


def _model_zoo(num_cols: list[str]) -> dict:
    """Trzy rodziny na tym samym (zinżynierowanym) zbiorze cech."""
    ridge = Pipeline(
        [
            (
                "prep",
                ColumnTransformer(
                    [
                        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
                        (
                            "num",
                            Pipeline(
                                [
                                    ("imp", SimpleImputer(strategy="median")),
                                    ("sc", StandardScaler()),
                                ]
                            ),
                            num_cols,
                        ),
                    ]
                ),
            ),
            ("ridge", Ridge(alpha=1.0)),
        ]
    )
    hist = Pipeline(
        [
            (
                "prep",
                ColumnTransformer(
                    [
                        (
                            "cat",
                            OrdinalEncoder(
                                handle_unknown="use_encoded_value", unknown_value=-1
                            ),
                            CATEGORICAL,
                        )
                    ],
                    remainder="passthrough",
                ),
            ),
            ("hist", HistGradientBoostingRegressor(random_state=42)),
        ]
    )
    lgbm = LGBMRegressor(
        n_estimators=500, learning_rate=0.05, num_leaves=31, random_state=42, verbose=-1
    )
    # (estimator, categorical_feature dla LightGBM lub None)
    return {
        "ridge": (ridge, None),
        "hist_gbr": (hist, None),
        "lightgbm": (lgbm, CATEGORICAL),
    }


def compare_model_families(model_input: pd.DataFrame, split: dict, opt: dict) -> dict:
    """Porównaj >=3 rodziny modeli na wspólnej 5-fold GroupKFold; loguj do MLflow."""
    mlflow = _setup_mlflow()
    X, y_log, groups = _train_view(model_input, split)
    num_cols = [c for c in X.columns if c not in CATEGORICAL]

    leaderboard = {}
    for name, (estimator, categorical) in _model_zoo(num_cols).items():
        rmse, std = _cv_rmse_pln(
            estimator, X, y_log, groups, opt["cv_folds"], categorical
        )
        leaderboard[name] = {"cv_rmse_pln": rmse, "cv_rmse_std": std}
        with _run(mlflow, f"compare_{name}"):
            mlflow.log_param("family", name)
            mlflow.log_metric("cv_rmse_pln", rmse)
            mlflow.log_metric("cv_rmse_std", std)
    return dict(sorted(leaderboard.items(), key=lambda kv: kv[1]["cv_rmse_pln"]))


def tune_lightgbm(model_input: pd.DataFrame, split: dict, opt: dict) -> dict:
    """Strojenie LightGBM Optuną (TPE + MedianPruner) na 5-fold GroupKFold; loguj study."""
    import optuna

    mlflow = _setup_mlflow()
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    X, y_log, groups = _train_view(model_input, split)
    n_splits = opt["cv_folds"]

    def objective(trial) -> float:
        params = {
            "objective": "regression",
            "metric": "rmse",
            "random_state": 42,
            "verbosity": -1,
            "n_estimators": 2000,
            "learning_rate": trial.suggest_float("learning_rate", 5e-3, 0.2, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 16, 256, log=True),
            "max_depth": trial.suggest_int("max_depth", 3, 12),
            "min_child_samples": trial.suggest_int("min_child_samples", 5, 200),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "subsample_freq": 1,
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
            "min_split_gain": trial.suggest_float("min_split_gain", 0.0, 0.5),
        }
        gkf = GroupKFold(n_splits=n_splits)
        scores, iters = [], []
        for tr, va in gkf.split(X, y_log, groups):
            model = LGBMRegressor(**params)
            model.fit(
                X.iloc[tr],
                y_log.iloc[tr],
                eval_set=[(X.iloc[va], y_log.iloc[va])],
                eval_metric="rmse",
                categorical_feature=CATEGORICAL,
                callbacks=[early_stopping(100, verbose=False), log_evaluation(0)],
            )
            best_it = model.best_iteration_ or params["n_estimators"]
            pred = np.expm1(model.predict(X.iloc[va], num_iteration=best_it))
            scores.append(
                np.sqrt(mean_squared_error(np.expm1(y_log.iloc[va].to_numpy()), pred))
            )
            iters.append(best_it)
        trial.set_user_attr("n_estimators", int(np.mean(iters)))
        return float(np.mean(scores))

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42),
        pruner=optuna.pruners.MedianPruner(),
    )
    study.optimize(objective, n_trials=opt["n_trials"])

    best_params = {
        "objective": "regression",
        "random_state": 42,
        "verbosity": -1,
        "n_estimators": int(study.best_trial.user_attrs["n_estimators"]),
        **study.best_params,
        "subsample_freq": 1,
    }
    with _run(mlflow, "optuna_lightgbm"):
        mlflow.log_params(study.best_params)
        mlflow.log_param("n_estimators_chosen", best_params["n_estimators"])
        mlflow.log_metric("best_cv_rmse_pln", float(study.best_value))
        mlflow.log_metric("n_trials", len(study.trials))
    return {"best_params": best_params, "best_cv_rmse": float(study.best_value)}


def register_champion(
    apartments_clean: pd.DataFrame,
    model_input: pd.DataFrame,
    tuning: dict,
    split: dict,
) -> dict:
    """Zbuduj, oceń i zarejestruj championa (Pipeline FE+model) w MLflow Registry."""
    from mlflow import MlflowClient
    from mlflow.models import infer_signature

    mlflow = _setup_mlflow()
    if (
        not apartments_clean["id"]
        .reset_index(drop=True)
        .equals(model_input["id"].reset_index(drop=True))
    ):
        raise ValueError("apartments_clean i model_input nie są wyrównane wierszami")

    train_idx, test_idx = _split_indices(model_input, split)
    raw = apartments_clean.drop(
        columns=["id", split["target"], "__month"], errors="ignore"
    )
    y_price = apartments_clean[split["target"]]
    X_train, X_test = raw.iloc[train_idx], raw.iloc[test_idx]
    y_train, y_test = y_price.iloc[train_idx], y_price.iloc[test_idx]

    champion = Pipeline(
        [
            ("fe", FunctionTransformer(engineer_features)),
            (
                "model",
                TransformedTargetRegressor(
                    regressor=LGBMRegressor(**tuning["best_params"]),
                    func=np.log1p,
                    inverse_func=np.expm1,
                ),
            ),
        ]
    )
    champion.fit(X_train, y_train)
    preds = champion.predict(X_test)
    metrics = regression_metrics(y_test.to_numpy(), preds)

    code_path = str(Path("src/apartment_prices").resolve())
    # Sygnatura DETERMINISTYCZNA i zgodna z kontraktem API: 11 cech wymaganych,
    # 15 opcjonalnych (required=False). Wymuszamy NaN w kolumnach opcjonalnych, aby
    # MLflow oznaczył je jako opcjonalne niezależnie od próbki (spójność z Pydantic).
    required_cols = {
        "city",
        "squareMeters",
        "rooms",
        "latitude",
        "longitude",
        "centreDistance",
        "ownership",
        "hasParkingSpace",
        "hasBalcony",
        "hasSecurity",
        "hasStorageRoom",
    }
    optional_cols = [c for c in X_test.columns if c not in required_cols]
    sig_example = X_test.head(20).copy()
    sig_example.loc[sig_example.index[0], optional_cols] = np.nan
    signature = infer_signature(sig_example, preds[:20])
    with _run(mlflow, "champion_lightgbm"):
        mlflow.log_params({f"lgbm_{k}": v for k, v in tuning["best_params"].items()})
        mlflow.log_metrics({f"holdout_{k}": v for k, v in metrics.items()})
        mlflow.log_metric("baseline_cv_rmse_pln", tuning["best_cv_rmse"])
        info = mlflow.sklearn.log_model(
            champion,
            name="model",
            signature=signature,
            input_example=X_test.head(2),
            code_paths=[code_path],
            registered_model_name=REGISTERED_MODEL,
        )

    # Promocja do aliasu 'production' tylko gdy holdout mieści się w ~5% CV-RMSE
    # ORAZ champion co najmniej dorównuje baseline (zabezpieczenie przed degeneracją,
    # np. niepełnym strojeniem Optuny). Inaczej alias zostaje na poprzedniej wersji.
    client = MlflowClient()
    promoted = (
        metrics["rmse"] <= tuning["best_cv_rmse"] * 1.05
        and metrics["r2"] >= MIN_PRODUCTION_R2
    )
    if promoted:
        client.set_registered_model_alias(
            REGISTERED_MODEL, "production", info.registered_model_version
        )
    return {
        **metrics,
        "registered_version": int(info.registered_model_version),
        "promoted_to_production": bool(promoted),
    }
