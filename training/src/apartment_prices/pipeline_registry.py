"""Rejestr pipeline'ów - automatyczne wykrywanie przez ``find_pipelines()``."""

from kedro.framework.project import find_pipelines
from kedro.pipeline import Pipeline


def register_pipelines() -> dict[str, Pipeline]:
    """Wykryj pipeline'y; domyślny (``__default__``) = baseline (dp -> fe -> modeling).

    Ciężki pipeline ``optimization`` (porównanie + Optuna + rejestracja) jest osobny -
    uruchamiany jawnie przez ``kedro run --pipeline optimization``.
    """
    pipelines = find_pipelines()
    pipelines["__default__"] = (
        pipelines["data_processing"]
        + pipelines["feature_engineering"]
        + pipelines["modeling"]
    )
    return pipelines
