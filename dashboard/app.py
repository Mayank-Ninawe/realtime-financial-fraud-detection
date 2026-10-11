"""Streamlit analyst dashboard for fraud alerts and case management."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"
CASES_PATH = Path("data/processed/cases.json")
STREAMED_TRANSACTIONS_PATH = Path("data/processed/streamed_transactions.json")

st.set_page_config(
    page_title="Fraud Detection Analyst Dashboard",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Real-Time Fraud Detection Dashboard")
st.caption(
    "Scores transactions through FastAPI, tracks analyst cases, "
    "and displays Kafka-streamed alerts."
)


def load_json_records(path: Path) -> list[dict]:
    """Load a JSON list from disk or return an empty list."""
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json_records(path: Path, records: list[dict]) -> None:
    """Persist records to a local JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=2)


def load_cases() -> list[dict]:
    """Load persisted analyst cases."""
    return load_json_records(CASES_PATH)


def save_cases(cases: list[dict]) -> None:
    """Persist analyst cases."""
    save_json_records(CASES_PATH, cases)


def create_case_from_prediction(
    prediction: dict,
    transaction: dict,
    source: str,
) -> dict:
    """Create a new analyst case record from a model prediction."""
    now = datetime.now(timezone.utc).isoformat()

    return {
        "transaction_id": prediction["transaction_id"],
        "fraud_probability": prediction["fraud_probability"],
        "risk_score": prediction["risk_score"],
        "is_alert": prediction["is_alert"],
        "recommended_action": prediction["recommended_action"],
        "transaction_details": transaction,
        "source": source,
        "case_status": "New",
        "analyst_feedback": "",
        "created_at": now,
        "updated_at": now,
    }


def add_case_if_missing(cases: list[dict], new_case: dict) -> bool:
    """Add a case only when its transaction ID has not been stored already."""
    existing_ids = {case["transaction_id"] for case in cases}

    if new_case["transaction_id"] in existing_ids:
        return False

    cases.append(new_case)
    return True


def get_streamed_alerts() -> list[dict]:
    """Return alert-generating scored events from Kafka consumer output."""
    streamed_records = load_json_records(STREAMED_TRANSACTIONS_PATH)

    return [
        record
        for record in streamed_records
        if record.get("prediction", {}).get("is_alert", False)
    ]


cases = load_cases()
streamed_alerts = get_streamed_alerts()

with st.sidebar:
    st.header("Score a transaction")

    transaction_id = st.text_input("Transaction ID", value="txn_demo_001")
    transaction_type = st.selectbox(
        "Transaction type",
        ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"],
    )
    amount = st.number_input("Amount", min_value=0.0, value=150000.0)
    sender_id = st.text_input("Sender account", value="C1000001")
    receiver_id = st.text_input("Receiver account", value="C2000001")
    sender_old_balance = st.number_input(
        "Sender balance before",
        min_value=0.0,
        value=200000.0,
    )
    sender_new_balance = st.number_input(
        "Sender balance after",
        min_value=0.0,
        value=50000.0,
    )
    receiver_old_balance = st.number_input(
        "Receiver balance before",
        min_value=0.0,
        value=0.0,
    )
    receiver_new_balance = st.number_input(
        "Receiver balance after",
        min_value=0.0,
        value=150000.0,
    )
    step = st.number_input("Simulation step", min_value=1, value=100)

    score_button = st.button("Score transaction", type="primary")

col1, col2, col3 = st.columns(3)
col1.metric("Stored analyst cases", len(cases))
col2.metric("Kafka-streamed alerts", len(streamed_alerts))
col3.metric(
    "Open cases",
    sum(case["case_status"] != "Resolved" for case in cases),
)

st.divider()

left_column, right_column = st.columns([2, 1])

with left_column:
    st.subheader("Manual transaction scoring")

    if score_button:
        payload = {
            "transaction_id": transaction_id,
            "step": int(step),
            "type": transaction_type,
            "amount": float(amount),
            "nameOrig": sender_id,
            "oldbalanceOrg": float(sender_old_balance),
            "newbalanceOrig": float(sender_new_balance),
            "nameDest": receiver_id,
            "oldbalanceDest": float(receiver_old_balance),
            "newbalanceDest": float(receiver_new_balance),
        }

        try:
            response = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
            response.raise_for_status()
            prediction = response.json()

            st.success("Prediction received from FastAPI service.")

            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("Risk score", f"{prediction['risk_score']:.2f}%")
            metric_col2.metric("Alert", "Yes" if prediction["is_alert"] else "No")
            metric_col3.metric(
                "Recommended action",
                prediction["recommended_action"],
            )

            st.json(prediction)

            new_case = create_case_from_prediction(
                prediction=prediction,
                transaction=payload,
                source="manual_api",
            )

            if add_case_if_missing(cases, new_case):
                save_cases(cases)
                st.info("Case created with status: New")
            else:
                st.info("A case already exists for this transaction ID.")

        except requests.exceptions.ConnectionError:
            st.error(
                "FastAPI service is not reachable. Start it with: "
                "`uvicorn api.main:app --app-dir . --port 8000`"
            )
        except requests.exceptions.HTTPError as error:
            st.error(f"API returned an error: {error.response.text}")
        except (KeyError, OSError, TypeError, ValueError) as error:
            st.error(f"Unexpected error: {error}")

with right_column:
    st.subheader("Service status")

    try:
        health_response = requests.get(f"{API_URL}/health", timeout=5)
        health_response.raise_for_status()
        st.success("FastAPI service is healthy.")
    except requests.exceptions.RequestException:
        st.error("FastAPI service is offline.")

st.divider()

st.subheader("Kafka-streamed fraud alerts")

if not streamed_alerts:
    st.info(
        "No streamed alerts found yet. Start the Kafka consumer and replay "
        "transactions with the producer."
    )
else:
    streamed_alert_rows = []

    for record in streamed_alerts:
        transaction = record["transaction"]
        prediction = record["prediction"]

        streamed_alert_rows.append(
            {
                "transaction_id": prediction["transaction_id"],
                "event_timestamp": record.get("event_timestamp"),
                "processed_at": record.get("processed_at"),
                "type": transaction["type"],
                "amount": transaction["amount"],
                "risk_score": prediction["risk_score"],
                "is_alert": prediction["is_alert"],
                "recommended_action": prediction["recommended_action"],
            }
        )

    streamed_alerts_df = pd.DataFrame(streamed_alert_rows).sort_values(
        "processed_at",
        ascending=False,
    )

    st.dataframe(streamed_alerts_df, use_container_width=True)

    if st.button("Create cases for streamed alerts"):
        created_count = 0

        for record in streamed_alerts:
            new_case = create_case_from_prediction(
                prediction=record["prediction"],
                transaction=record["transaction"],
                source="kafka_stream",
            )

            if add_case_if_missing(cases, new_case):
                created_count += 1

        if created_count > 0:
            save_cases(cases)
            st.success(f"Created {created_count} case(s) from streamed alerts.")
        else:
            st.info("Cases already exist for all streamed alerts.")

st.divider()

st.subheader("Analyst cases")

if not cases:
    st.info("No cases yet. Score a transaction or create cases from streamed alerts.")
else:
    cases_df = pd.DataFrame(cases)
    display_columns = [
        "transaction_id",
        "source",
        "risk_score",
        "is_alert",
        "recommended_action",
        "case_status",
        "created_at",
    ]
    st.dataframe(cases_df[display_columns], use_container_width=True)

    st.subheader("Update case")

    selected_transaction_id = st.selectbox(
        "Select transaction",
        options=[case["transaction_id"] for case in cases],
    )

    selected_index = next(
        index
        for index, case in enumerate(cases)
        if case["transaction_id"] == selected_transaction_id
    )
    selected_case = cases[selected_index]

    case_statuses = ["New", "Under Review", "Resolved"]
    selected_status = selected_case.get("case_status", "New")

    if selected_status not in case_statuses:
        selected_status = "New"

    new_status = st.selectbox(
        "Case status",
        case_statuses,
        index=case_statuses.index(selected_status),
    )
    feedback = st.text_area(
        "Analyst feedback",
        value=selected_case.get("analyst_feedback", ""),
    )

    if st.button("Save case update"):
        cases[selected_index]["case_status"] = new_status
        cases[selected_index]["analyst_feedback"] = feedback
        cases[selected_index]["updated_at"] = datetime.now(
            timezone.utc
        ).isoformat()
        save_cases(cases)
        st.success("Case updated successfully.")