"""Consume Kafka transaction events and score them through FastAPI."""

from __future__ import annotations

import json
import signal
from datetime import datetime, timezone

import requests
from confluent_kafka import Consumer, KafkaError

from streaming.config import (
    CONSUMER_ERRORS_PATH,
    FASTAPI_PREDICT_URL,
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_CONSUMER_GROUP,
    KAFKA_TOPIC,
    STREAMED_TRANSACTIONS_PATH,
)

RUNNING = True


def stop_consumer(_signal_number, _frame) -> None:
    """Handle Ctrl+C gracefully."""
    global RUNNING
    RUNNING = False


def load_json_records(path) -> list[dict]:
    """Load JSON list data or return an empty list when absent."""
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def append_json_record(path, record: dict) -> None:
    """Append one record to a local JSON list."""
    path.parent.mkdir(parents=True, exist_ok=True)
    records = load_json_records(path)
    records.append(record)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=2)


def validate_event(event: dict) -> dict:
    """Validate basic Kafka event structure and return transaction payload."""
    if event.get("event_type") != "transaction":
        raise ValueError("Unsupported event_type. Expected 'transaction'.")

    transaction = event.get("transaction")
    if not isinstance(transaction, dict):
        raise ValueError("Event must contain a transaction object.")

    required_fields = {
        "transaction_id",
        "step",
        "type",
        "amount",
        "nameOrig",
        "oldbalanceOrg",
        "newbalanceOrig",
        "nameDest",
        "oldbalanceDest",
        "newbalanceDest",
    }

    missing_fields = required_fields - set(transaction)
    if missing_fields:
        raise ValueError(
            f"Transaction is missing fields: {sorted(missing_fields)}"
        )

    return transaction


def process_message(message_value: bytes) -> dict:
    """Decode, validate, score, and persist a Kafka transaction event."""
    event = json.loads(message_value.decode("utf-8"))
    transaction = validate_event(event)

    response = requests.post(
        FASTAPI_PREDICT_URL,
        json=transaction,
        timeout=15,
    )
    response.raise_for_status()

    prediction = response.json()

    processed_record = {
        "event_id": event.get("event_id"),
        "event_timestamp": event.get("event_timestamp"),
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "transaction": transaction,
        "prediction": prediction,
    }

    append_json_record(STREAMED_TRANSACTIONS_PATH, processed_record)
    return processed_record


def run_consumer() -> None:
    """Continuously consume and score events until Ctrl+C."""
    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": KAFKA_CONSUMER_GROUP,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
        }
    )

    signal.signal(signal.SIGINT, stop_consumer)
    signal.signal(signal.SIGTERM, stop_consumer)

    consumer.subscribe([KAFKA_TOPIC])

    print(
        f"Consumer started. Listening to topic '{KAFKA_TOPIC}'. "
        "Press Ctrl+C to stop."
    )

    try:
        while RUNNING:
            message = consumer.poll(1.0)

            if message is None:
                continue

            if message.error():
                if message.error().code() == KafkaError._PARTITION_EOF:
                    continue
                print(f"Kafka consumer error: {message.error()}")
                continue

            try:
                result = process_message(message.value())
                prediction = result["prediction"]
                print(
                    f"Processed {prediction['transaction_id']}: "
                    f"risk={prediction['risk_score']}%, "
                    f"alert={prediction['is_alert']}"
                )
            except Exception as error:
                error_record = {
                    "received_at": datetime.now(timezone.utc).isoformat(),
                    "error": str(error),
                    "raw_message": message.value().decode(
                        "utf-8", errors="replace"
                    ),
                }
                append_json_record(CONSUMER_ERRORS_PATH, error_record)
                print(f"Failed to process message: {error}")

    finally:
        consumer.close()
        print("Consumer stopped.")


if __name__ == "__main__":
    run_consumer()