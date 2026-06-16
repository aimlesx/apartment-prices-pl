"""Serwis inferencyjny FastAPI z metrykami Prometheus."""

import logging

from fastapi import FastAPI, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

from apartment_serving.model import get_model
from apartment_serving.schemas import ApartmentFeatures, PricePrediction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("apartment_serving")

app = FastAPI(title="Apartment Price Predictor", version="1.0.0")

# --- Metryki Prometheus ---
PREDICTIONS = Counter("model_predictions_total", "Liczba obsłużonych predykcji")
PREDICTION_LATENCY = Histogram(
    "model_prediction_latency_seconds", "Czas obsługi predykcji [s]"
)
PREDICTED_PRICE = Histogram(
    "model_predicted_price_pln",
    "Rozkład przewidywanych cen [PLN]",
    buckets=(2e5, 4e5, 6e5, 8e5, 1e6, 1.5e6, 2e6, 3e6),
)
INPUT_SQM = Histogram(
    "model_input_square_meters",
    "Rozkład metrażu wejść [m2] — sygnał driftu danych",
    buckets=(25, 40, 55, 70, 85, 100, 120, 150),
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness/readiness — sprawdza, czy model daje się załadować."""
    get_model()
    return {"status": "ok"}


@app.post("/predict", response_model=PricePrediction)
def predict(features: ApartmentFeatures) -> PricePrediction:
    """Przewidź cenę mieszkania (PLN) i zarejestruj metryki/log dla monitoringu."""
    model = get_model()
    with PREDICTION_LATENCY.time():
        price = float(model.predict(features.to_frame())[0])

    PREDICTIONS.inc()
    PREDICTED_PRICE.observe(price)
    INPUT_SQM.observe(features.squareMeters)
    logger.info(
        "prediction price_pln=%.0f city=%s squareMeters=%.1f",
        price,
        features.city,
        features.squareMeters,
    )
    return PricePrediction(price_pln=round(price, 2))


@app.get("/metrics")
def metrics() -> Response:
    """Eksport metryk dla Prometheusa (bez przekierowania — scrape działa wprost)."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
