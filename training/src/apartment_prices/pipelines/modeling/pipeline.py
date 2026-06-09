"""Pipeline modeling - podział, trening i ewaluacja."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import evaluate_model, split_data, train_model


def create_pipeline(**kwargs) -> Pipeline:
    """Złóż węzły podziału, treningu i ewaluacji."""
    return pipeline(
        [
            node(
                func=split_data,
                inputs=["model_input", "params:split"],
                outputs=["X_train", "X_test", "y_train", "y_test"],
                name="split_data",
            ),
            node(
                func=train_model,
                inputs=["X_train", "y_train", "params:model"],
                outputs="model",
                name="train_model",
            ),
            node(
                func=evaluate_model,
                inputs=["model", "X_test", "y_test"],
                outputs="metrics",
                name="evaluate_model",
            ),
        ]
    )
