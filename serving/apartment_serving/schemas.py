"""Schematy żądania/odpowiedzi API (Pydantic) — kontrakt 26 cech surowych.

Nazwy pól w API są w camelCase (jak kolumny datasetu), aby ``to_frame`` produkował
ramkę 1:1 zgodną z sygnaturą modelu. Wartości logiczne podajemy jako
``true/false`` i mapujemy na ``"yes"/"no"`` (format danych treningowych).
Pola opcjonalne (``None``) stają się ``NaN``/``"missing"`` — model obsługuje je natywnie.
"""

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

_BOOL_COLS = [
    "hasParkingSpace",
    "hasBalcony",
    "hasElevator",
    "hasSecurity",
    "hasStorageRoom",
]

# Kolumny numeryczne — rzutujemy na float64, by zgadzały się z sygnaturą modelu
# (dane treningowe są float; ścisła walidacja MLflow nie rzutuje int64 → float64).
_NUMERIC_COLS = [
    "squareMeters",
    "rooms",
    "latitude",
    "longitude",
    "centreDistance",
    "floor",
    "floorCount",
    "buildYear",
    "poiCount",
    "schoolDistance",
    "clinicDistance",
    "postOfficeDistance",
    "kindergartenDistance",
    "restaurantDistance",
    "collegeDistance",
    "pharmacyDistance",
]


class ApartmentFeatures(BaseModel):
    """Cechy mieszkania (wejście modelu). camelCase = nazwy kolumn modelu."""

    model_config = ConfigDict(populate_by_name=True)

    # --- wymagane ---
    city: str = Field(..., examples=["warszawa"])
    squareMeters: float = Field(..., gt=0, examples=[52.0])  # noqa: N815
    rooms: int = Field(..., gt=0, examples=[3])
    latitude: float = Field(..., examples=[52.23])
    longitude: float = Field(..., examples=[21.0])
    centreDistance: float = Field(..., ge=0, examples=[3.4])  # noqa: N815
    ownership: str = Field(..., examples=["condominium"])
    hasParkingSpace: bool = Field(..., examples=[True])  # noqa: N815
    hasBalcony: bool = Field(..., examples=[True])  # noqa: N815
    hasSecurity: bool = Field(..., examples=[False])  # noqa: N815
    hasStorageRoom: bool = Field(..., examples=[True])  # noqa: N815

    # --- opcjonalne (naturalnie brakujące) ---
    type: str | None = Field(None, examples=["blockOfFlats"])
    floor: float | None = Field(None, examples=[2])
    floorCount: float | None = Field(None, examples=[5])  # noqa: N815
    buildYear: float | None = Field(None, examples=[2010])  # noqa: N815
    buildingMaterial: str | None = Field(None, examples=["brick"])  # noqa: N815
    condition: str | None = Field(None, examples=["premium"])
    hasElevator: bool | None = Field(None, examples=[True])  # noqa: N815
    poiCount: float | None = Field(None, examples=[35])  # noqa: N815
    schoolDistance: float | None = Field(None, examples=[0.3])  # noqa: N815
    clinicDistance: float | None = Field(None, examples=[0.5])  # noqa: N815
    postOfficeDistance: float | None = Field(None, examples=[0.4])  # noqa: N815
    kindergartenDistance: float | None = Field(None, examples=[0.2])  # noqa: N815
    restaurantDistance: float | None = Field(None, examples=[0.1])  # noqa: N815
    collegeDistance: float | None = Field(None, examples=[1.2])  # noqa: N815
    pharmacyDistance: float | None = Field(None, examples=[0.3])  # noqa: N815

    def to_frame(self) -> pd.DataFrame:
        """Zamień na jednowierszowy DataFrame zgodny z wejściem modelu."""
        row = self.model_dump()
        for col in _BOOL_COLS:
            value = row.get(col)
            row[col] = None if value is None else ("yes" if value else "no")
        frame = pd.DataFrame([row])
        frame[_NUMERIC_COLS] = frame[_NUMERIC_COLS].astype("float64")
        return frame


class PricePrediction(BaseModel):
    """Odpowiedź — przewidywana cena w PLN."""

    price_pln: float
