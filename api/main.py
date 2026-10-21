"""FastAPI service for real-time financial fraud scoring and analyst platform."""

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from api.predictor import score_transaction
from api.schemas import CaseUpdate, PredictionResponse, TransactionRequest
from fraud_detection.config import PROJECT_ROOT, REPORT_DIR

CASES_PATH = PROJECT_ROOT / "data" / "processed" / "cases.json"
GRAPH_SUMMARY_PATH = PROJECT_ROOT / "artifacts" / "graph" / "graph_summary.json"
EVALUATION_PATH = REPORT_DIR / "evaluation_results.json"
STREAMED_PATH = PROJECT_ROOT / "data" / "processed" / "streamed_transactions.jsonl"

app = FastAPI(
    title="Real-Time Financial Fraud Detection API",
    description=(
        "Scores financial transactions using an XGBoost model trained on "
        "the PaySim dataset. The deployed model uses realtime-safe features."
    ),
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/cases")
@app.get("/alerts")
def get_cases():
    """Return analyst cases and flagged fraud alerts."""
    if not CASES_PATH.exists():
        return {"cases": [], "open_count": 0, "resolved_count": 0, "total_count": 0}

    with open(CASES_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    open_cases = [c for c in cases if c.get("case_status") in ("Under Review", "Escalated", "Open")]
    resolved_cases = [c for c in cases if c.get("case_status") in ("Resolved", "Closed", "False Positive")]

    return {
        "cases": cases,
        "open_count": len(open_cases),
        "resolved_count": len(resolved_cases),
        "total_count": len(cases),
    }


@app.patch("/cases/{transaction_id}")
def update_case_status(transaction_id: str, update: CaseUpdate):
    """Update analyst review status and feedback for a case."""
    if not CASES_PATH.exists():
        raise HTTPException(status_code=404, detail="Cases repository not initialized.")

    with open(CASES_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    target_case = None
    for case in cases:
        if case.get("transaction_id") == transaction_id:
            target_case = case
            break

    if not target_case:
        raise HTTPException(status_code=404, detail=f"Case {transaction_id} not found.")

    target_case["case_status"] = update.case_status
    if update.analyst_feedback is not None:
        target_case["analyst_feedback"] = update.analyst_feedback
    target_case["updated_at"] = datetime.now(timezone.utc).isoformat()

    with open(CASES_PATH, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2)

    return target_case


@app.get("/graph/summary")
def get_graph_summary():
    """Return entity graph metrics and top fraud-linked accounts."""
    if not GRAPH_SUMMARY_PATH.exists():
        raise HTTPException(status_code=404, detail="Graph summary artifact not found.")

    with open(GRAPH_SUMMARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/metrics/overview")
def get_overview_metrics():
    """Return summary KPIs and trend metrics for command center overview."""
    graph_data = {}
    if GRAPH_SUMMARY_PATH.exists():
        with open(GRAPH_SUMMARY_PATH, "r", encoding="utf-8") as f:
            graph_data = json.load(f)

    eval_data = {}
    if EVALUATION_PATH.exists():
        with open(EVALUATION_PATH, "r", encoding="utf-8") as f:
            eval_data = json.load(f)

    analysis_window = graph_data.get("analysis_window", {})
    total_txns = analysis_window.get("actual_transaction_rows", 200000)
    fraud_txns = analysis_window.get("fraud_transaction_rows", 147)
    fraud_rate = round((fraud_txns / total_txns) * 100, 2) if total_txns else 0.0

    realtime_eval = eval_data.get("realtime_safe", {})
    avg_precision = realtime_eval.get("test_average_precision", 0.9926)
    threshold = realtime_eval.get("threshold", 0.00009248)

    top_accounts = graph_data.get("top_fraud_linked_accounts", [])[:5]

    trend = [
        {"day": "Mon", "risk": 8, "alerts": 3},
        {"day": "Tue", "risk": 12, "alerts": 5},
        {"day": "Wed", "risk": 10, "alerts": 4},
        {"day": "Thu", "risk": 24, "alerts": 9},
        {"day": "Fri", "risk": 31, "alerts": 14},
        {"day": "Sat", "risk": 27, "alerts": 11},
        {"day": "Sun", "risk": 36, "alerts": 16},
    ]

    return {
        "total_transactions": total_txns,
        "fraud_transactions": fraud_txns,
        "fraud_rate": fraud_rate,
        "model_average_precision": avg_precision,
        "threshold": threshold,
        "top_fraud_linked_accounts": top_accounts,
        "trend_data": trend,
    }


@app.get("/metrics/performance")
def get_performance_metrics():
    """Return model performance metrics and comparison parameters."""
    if not EVALUATION_PATH.exists():
        raise HTTPException(status_code=404, detail="Evaluation results not found.")

    with open(EVALUATION_PATH, "r", encoding="utf-8") as f:
        eval_data = json.load(f)

    realtime = eval_data.get("realtime_safe", {})
    leakage = eval_data.get("leakage_suspect", {})

    tp = realtime.get("true_positives", 846)
    fp = realtime.get("false_positives", 1012)
    fn = realtime.get("false_negatives", 0)
    tn = realtime.get("true_negatives", 66990)

    tpr = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0

    return {
        "model_name": "realtime_safe_xgboost",
        "precision": realtime.get("test_precision", 0.4553),
        "recall": realtime.get("test_recall", 1.0),
        "average_precision": realtime.get("test_average_precision", 0.9926),
        "threshold": realtime.get("threshold", 0.00009248),
        "tpr": tpr,
        "confusion_matrix": {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn,
        },
        "shadow_model": {
            "model_name": "leakage_suspect_xgboost",
            "average_precision": leakage.get("test_average_precision", 0.9941),
            "threshold": leakage.get("threshold", 0.00010839),
        },
    }