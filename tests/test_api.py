"""Tests for the fraud scoring API."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_predict_valid_transaction():
    payload = {
        "transaction_id": "txn_test_001",
        "step": 100,
        "type": "TRANSFER",
        "amount": 150000.0,
        "nameOrig": "C1000001",
        "oldbalanceOrg": 200000.0,
        "newbalanceOrig": 50000.0,
        "nameDest": "C2000001",
        "oldbalanceDest": 0.0,
        "newbalanceDest": 150000.0,
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    result = response.json()

    assert result["transaction_id"] == "txn_test_001"
    assert 0.0 <= result["fraud_probability"] <= 1.0
    assert 0.0 <= result["risk_score"] <= 100.0
    assert isinstance(result["is_alert"], bool)
    assert result["model_name"] == "realtime_safe_xgboost"


def test_predict_invalid_amount():
    payload = {
        "transaction_id": "txn_test_002",
        "step": 100,
        "type": "TRANSFER",
        "amount": -10.0,
        "nameOrig": "C1000001",
        "oldbalanceOrg": 200000.0,
        "newbalanceOrig": 50000.0,
        "nameDest": "C2000001",
        "oldbalanceDest": 0.0,
        "newbalanceDest": 150000.0,
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 422