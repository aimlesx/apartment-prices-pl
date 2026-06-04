"""Węzły pipeline'u data_processing: pozyskanie i scalenie danych źródłowych."""

from collections.abc import Callable

import pandas as pd

SALE_PREFIX = "apartments_pl_"


def ingest_apartments(
    partitions: dict[str, Callable[[], pd.DataFrame]],
) -> pd.DataFrame:
    """Scal miesięczne pliki sprzedaży (``apartments_pl_*``) w jedną ramkę.

    Pliki najmu (``apartments_rent_*``) są celowo pomijane - projekt dotyczy cen
    sprzedaży. Z nazwy pliku wyprowadzamy kolumnę ``__month`` (format ``RRRR-MM``),
    przydatną do deduplikacji (keep-last), walidacji czasowej i analizy sezonowości.
    Kolumna jest odrzucana przed modelowaniem (nie jest cechą - API jej nie zna).
    """
    frames: list[pd.DataFrame] = []
    for key in sorted(partitions):
        if not key.startswith(SALE_PREFIX):
            continue
        df = partitions[key]()
        df["__month"] = key.removeprefix(SALE_PREFIX).replace("_", "-")
        frames.append(df)
    if not frames:
        raise ValueError(
            f"Nie znaleziono plików sprzedaży ({SALE_PREFIX}*.csv) w data/01_raw"
        )
    return pd.concat(frames, ignore_index=True)
