"""Węzły pipeline'u data_processing: pozyskanie, scalenie i czyszczenie danych."""

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


def deduplicate_and_clean(ingested: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Deduplikacja keep-last po ``id`` + filtr własności + asercje jakości.

    To samo ogłoszenie powtarza się w wielu miesiącach - zostawiamy najnowszy rekord
    (najświeższa cena rynkowa). Zostawiamy tylko własności sprzedażowe i ceny w
    oczekiwanym zakresie (dane Kaggle są wstępnie przycięte do 150k-3,25M PLN).
    """
    df = (
        ingested.sort_values(["id", "__month"], kind="mergesort")
        .drop_duplicates(subset="id", keep="last")
        .reset_index(drop=True)
    )
    df = df[df["ownership"].isin(params["sale_ownership"])].reset_index(drop=True)
    df = df[df["price"].between(params["price_min"], params["price_max"])]
    df = df.reset_index(drop=True)
    if len(df) != df["id"].nunique():
        raise ValueError("Po deduplikacji powinien być dokładnie 1 wiersz na id")
    return df
