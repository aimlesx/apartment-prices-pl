"""Testy rejestru pipeline'ów i pozyskania danych."""

from apartment_prices.pipelines.data_processing import create_pipeline


def test_data_processing_pipeline_has_ingest_node():
    """Pipeline data_processing musi zawierać węzeł pozyskania danych."""
    pipe = create_pipeline()
    node_names = {node.name for node in pipe.nodes}
    assert "ingest_apartments" in node_names
