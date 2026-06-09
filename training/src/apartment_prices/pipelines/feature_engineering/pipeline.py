"""Pipeline feature_engineering - inżynieria cech."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import engineer_features


def create_pipeline(**kwargs) -> Pipeline:
    """Zbuduj macierz cech modelu (z zachowaniem ``id`` i ``price`` do podziału)."""
    return pipeline(
        [
            node(
                func=engineer_features,
                inputs="apartments_clean",
                outputs="model_input",
                name="engineer_features",
            ),
        ]
    )
