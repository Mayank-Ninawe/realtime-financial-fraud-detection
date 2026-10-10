"""FastAPI service for real-time financial fraud scoring."""

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from api.predictor import score_transaction
from api.schemas import PredictionResponse, TransactionRequest

app = FastAPI(
    title="Real-Time Financial Fraud Detection API",
    description=(
        "Scores financial transactions using an XGBoost model trained on "
        "the PaySim dataset. The deployed model uses realtime-safe features."
    ),
    version="0.1.0",
)


@app.get("/health")
def health_check():
    """Return service health status."""
    return {"status": "healthy", "service": "fraud-detection-api"}


@app.post("/predict", response_model=PredictionResponse)
def predict_transaction(transaction: TransactionRequest) -> PredictionResponse:
    """Score a single financial transaction for fraud risk."""
    try:
        result = score_transaction(transaction.model_dump())
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error))
    except (ValidationError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error))

    return PredictionResponse(**result)