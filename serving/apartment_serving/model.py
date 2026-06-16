"""Ładowanie modelu (MLflow pyfunc) — z Registry (lokalnie) albo z katalogu w obrazie Dockera.

- Lokalnie: ``MODEL_URI=models:/apartment-price-model@production`` +
  ``MLFLOW_TRACKING_URI=sqlite:///.../training/mlflow.db`` (rejestr SQLite).
- W kontenerze: ``MODEL_URI=/app/model`` — samodzielny artefakt (z kodem cech przez
  ``code_paths``) wbudowany w obraz; nie wymaga Kedro ani rejestru.
"""

import os
from functools import lru_cache

DEFAULT_MODEL_URI = "models:/apartment-price-model@production"


@lru_cache(maxsize=1)
def get_model():
    """Załaduj model raz na proces (cache)."""
    import mlflow

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_registry_uri(os.getenv("MLFLOW_REGISTRY_URI", tracking_uri))
    return mlflow.pyfunc.load_model(os.getenv("MODEL_URI", DEFAULT_MODEL_URI))
