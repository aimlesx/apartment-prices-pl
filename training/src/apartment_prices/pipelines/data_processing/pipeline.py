"""Pipeline data_processing - pozyskanie, scalenie i czyszczenie danych."""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import deduplicate_and_clean, ingest_apartments


def create_pipeline(**kwargs) -> Pipeline:
    """Złóż węzły pozyskania i czyszczenia danych."""
    return pipeline(
        [
            node(
                func=ingest_apartments,
                inputs="apartments_raw_partitions",
                outputs="apartments_ingested",
                name="ingest_apartments",
            ),
            node(
                func=deduplicate_and_clean,
                inputs=["apartments_ingested", "params:cleaning"],
                outputs="apartments_clean",
                name="deduplicate_and_clean",
            ),
        ]
    )
