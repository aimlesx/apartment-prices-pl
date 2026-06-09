"""Węzły pipeline'u feature_engineering - inżynieria cech.

``engineer_features`` to **jedno źródło prawdy** kontraktu cech: ta sama funkcja
jest używana w notebooku baseline, w pipeline Kedro oraz (przez ``FunctionTransformer``)
w artefakcie modelu serwowanym przez FastAPI - eliminuje to train/serve skew.
Funkcja jest czysta i nie wymaga ``id``/``price`` (przy serwowaniu ich nie ma);
kolumny te, jeśli obecne, przechodzą bez zmian i są odrzucane dopiero przy podziale.
"""

import pandas as pd

REFERENCE_YEAR = 2024
CATEGORICAL = ["city", "type", "ownership", "buildingMaterial", "condition"]
BOOL_COLS = [
    "hasParkingSpace",
    "hasBalcony",
    "hasElevator",
    "hasSecurity",
    "hasStorageRoom",
]
POI_COLS = [
    "schoolDistance",
    "clinicDistance",
    "postOfficeDistance",
    "kindergartenDistance",
    "restaurantDistance",
    "collegeDistance",
    "pharmacyDistance",
]
MISSING_FLAG_COLS = ["floor", "buildYear", "type", "buildingMaterial", "condition"]


def engineer_features(clean: pd.DataFrame) -> pd.DataFrame:
    """Zbuduj cechy modelu z oczyszczonych danych (kontrakt cech).

    - booly ``yes/no`` -> ``1/0`` (brak zostaje ``NaN``),
    - cechy domenowe: ``age``, ``floor_ratio``, ``rooms_per_m2``, flagi pięter,
      agregaty odległości POI, ``amenity_score``,
    - flagi ``*_is_missing`` (brak niesie sygnał),
    - kolumny kategoryczne: ``NaN`` -> poziom ``"missing"`` + dtype ``category``
      (natywna obsługa w LightGBM, bez one-hot).
    """
    X = clean.copy()
    for col in BOOL_COLS:
        X[col] = X[col].map({"yes": 1, "no": 0})

    X["age"] = REFERENCE_YEAR - X["buildYear"]
    X["floor_ratio"] = X["floor"] / X["floorCount"]
    X["rooms_per_m2"] = X["rooms"] / X["squareMeters"]
    X["is_top_floor"] = (X["floor"] == X["floorCount"]).astype(int)
    X["is_ground_floor"] = (X["floor"] == 0).astype(int)
    X["min_amenity_dist"] = X[POI_COLS].min(axis=1)
    X["mean_amenity_dist"] = X[POI_COLS].mean(axis=1)
    X["amenity_score"] = X[BOOL_COLS].fillna(0).sum(axis=1)

    for col in MISSING_FLAG_COLS:
        X[f"{col}_is_missing"] = X[col].isna().astype(int)

    for col in CATEGORICAL:
        X[col] = (
            X[col].astype("object").where(X[col].notna(), "missing").astype("category")
        )

    return X.drop(columns=["__month"], errors="ignore")
