"""Pipeline data_processing - pozyskanie i scalenie danych."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import ingest_apartments


def create_pipeline(**kwargs) -> Pipeline:
    """Złóż węzły pozyskania danych."""
    return pipeline(
        [
            node(
                func=ingest_apartments,
                inputs="apartments_raw_partitions",
                outputs="apartments_ingested",
                name="ingest_apartments",
            ),
        ]
    )
