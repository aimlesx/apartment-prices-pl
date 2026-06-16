"""Testy API — model zamockowany (CI nie wymaga MLflow ani wytrenowanego modelu)."""

from apartment_serving.schemas import ApartmentFeatures
from fastapi.testclient import TestClient

REQUIRED_PAYLOAD = {
    "city": "warszawa",
    "squareMeters": 52,
    "rooms": 3,
    "latitude": 52.2,
    "longitude": 21.0,
    "centreDistance": 3.4,
    "ownership": "condominium",
    "hasParkingSpace": True,
    "hasBalcony": True,
    "hasSecurity": False,
    "hasStorageRoom": True,
}


class _DummyModel:
    def predict(self, frame):
        return [500_000.0]


def test_health_and_predict(monkeypatch):
    from apartment_serving import main

    monkeypatch.setattr(main, "get_model", lambda: _DummyModel())
    client = TestClient(main.app)

    assert client.get("/health").json() == {"status": "ok"}

    resp = client.post("/predict", json=REQUIRED_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["price_pln"] == 500_000.0


def test_predict_rejects_missing_required():
    from apartment_serving import main

    monkeypatch_client = TestClient(main.app)
    bad = {k: v for k, v in REQUIRED_PAYLOAD.items() if k != "squareMeters"}
    assert monkeypatch_client.post("/predict", json=bad).status_code == 422


def test_to_frame_contract():
    features = ApartmentFeatures(**REQUIRED_PAYLOAD)
    frame = features.to_frame()
    assert frame.shape[1] == 26  # 11 wymaganych + 15 opcjonalnych
    assert frame["hasParkingSpace"].iloc[0] == "yes"
    assert frame["hasSecurity"].iloc[0] == "no"
    assert frame["floor"].isna().iloc[0]  # opcjonalne -> NaN
