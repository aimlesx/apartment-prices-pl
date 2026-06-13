"""Pipeline optimization - porównanie modeli, HPO i rejestracja championa (etap 4)."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import compare_model_families, register_champion, tune_lightgbm


def create_pipeline(**kwargs) -> Pipeline:
    """Złóż węzły: leaderboard -> strojenie LightGBM -> rejestracja championa."""
    return pipeline(
        [
            node(
                func=compare_model_families,
                inputs=["model_input", "params:split", "params:optimization"],
                outputs="leaderboard",
                name="compare_model_families",
            ),
            node(
                func=tune_lightgbm,
                inputs=["model_input", "params:split", "params:optimization"],
                outputs="tuning_result",
                name="tune_lightgbm",
            ),
            node(
                func=register_champion,
                inputs=[
                    "apartments_clean",
                    "model_input",
                    "tuning_result",
                    "params:split",
                ],
                outputs="optimized_metrics",
                name="register_champion",
            ),
        ]
    )
