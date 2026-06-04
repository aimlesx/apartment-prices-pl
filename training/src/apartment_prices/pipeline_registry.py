"""Rejestr pipeline'ów - automatyczne wykrywanie przez ``find_pipelines()``."""

from kedro.framework.project import find_pipelines
from kedro.pipeline import Pipeline


def register_pipelines() -> dict[str, Pipeline]:
    """Wykryj pipeline'y w pakiecie i złóż domyślny (``__default__``) jako ich sumę."""
    pipelines = find_pipelines()
    pipelines["__default__"] = sum(pipelines.values(), Pipeline([]))
    return pipelines
