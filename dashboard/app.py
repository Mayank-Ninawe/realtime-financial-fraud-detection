"""Streamlit analyst dashboard for fraud alerts and case management."""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"
CASES_PATH = Path("data/processed/cases.json")

st.set_page_config(
    page_title="Fraud Detection Analyst Dashboard",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Real-Time Fraud Detection Dashboard")
st.caption(
    "Scores transactions through the FastAPI service and manages analyst cases."
)


def load_cases() -> list[dict]:
    """Load persisted analyst cases from local JSON storage."""
    if CASES_PATH.exists():
        with open(CASES_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    return []


def save_cases(cases: list[dict]) -> None:
    """Persist analyst cases locally."""
    CASES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CASES_PATH, "w", encoding="utf-8") as file:
        json.dump(cases, file, indent=2)


cases = load_cases()

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
        "Sender balance before", min_value=0.0, value=200000.0
    )
    sender_new_balance = st.number_input(
        "Sender balance after", min_value=0.0, value=50000.0
    )
    receiver_old_balance = st.number_input(
        "Receiver balance before", min_value=0.0, value=0.0
    )
    receiver_new_balance = st.number_input(
        "Receiver balance after", min_value=0.0, value=150000.0
    )
    step = st.number_input("Simulation step", min_value=1, value=100)

    score_button = st.button("Score transaction", type="primary")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Transaction scoring")

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
            metric_col1.metric(
                "Risk score",
                f"{prediction['risk_score']:.2f}%",
            )
            metric_col2.metric(
                "Alert",
                "Yes" if prediction["is_alert"] else "No",
            )
            metric_col3.metric(
                "Recommended action",
                prediction["recommended_action"],
            )

            st.json(prediction)

            cases.append(
                {
                    "transaction_id": prediction["transaction_id"],
                    "fraud_probability": prediction["fraud_probability"],
                    "risk_score": prediction["risk_score"],
                    "is_alert": prediction["is_alert"],
                    "recommended_action": prediction["recommended_action"],
                    "transaction_details": payload,
                    "case_status": "New",
                    "analyst_feedback": "",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )
            save_cases(cases)
            st.info("Case created with status: New")

        except requests.exceptions.ConnectionError:
            st.error(
                "FastAPI service is not reachable. Start it with: "
                "`uvicorn api.main:app --reload --port 8000`"
            )
        except requests.exceptions.HTTPError as error:
            st.error(f"API returned an error: {error.response.text}")
        except Exception as error:
            st.error(f"Unexpected error: {error}")

with col2:
    st.subheader("Service status")

    try:
        health_response = requests.get(f"{API_URL}/health", timeout=5)
        health_response.raise_for_status()
        st.success("FastAPI service is healthy.")
    except requests.exceptions.RequestException:
        st.error("FastAPI service is offline.")

st.subheader("Analyst cases")

if not cases:
    st.info("No cases yet. Score a transaction to create one.")
else:
    cases_df = pd.DataFrame(cases)
    display_columns = [
        "transaction_id",
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

    new_status = st.selectbox(
        "Case status",
        ["New", "Under Review", "Resolved"],
        index=["New", "Under Review", "Resolved"].index(
            selected_case["case_status"]
        ),
    )
    feedback = st.text_area(
        "Analyst feedback",
        value=selected_case["analyst_feedback"],
    )

    if st.button("Save case update"):
        cases[selected_index]["case_status"] = new_status
        cases[selected_index]["analyst_feedback"] = feedback
        cases[selected_index]["updated_at"] = datetime.utcnow().isoformat()
        save_cases(cases)
        st.success("Case updated successfully.")