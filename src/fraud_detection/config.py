"""Central configuration for data paths, splits, and modeling."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "PS_20174392719_1491204439457_log.csv"
MODEL_DIR = PROJECT_ROOT / "models"
REPORT_DIR = PROJECT_ROOT / "reports"

RANDOM_SEED = 42

TARGET_COLUMN = "isFraud"
TIME_COLUMN = "step"

BASE_FEATURES = [
    "type",
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
]

DERIVED_FEATURES = [
    "sender_balance_change",
    "receiver_balance_change",
    "amount_to_sender_old_balance",
    "amount_to_receiver_old_balance",
    "is_transfer_or_cash_out",
]

CATEGORICAL_FEATURES = ["type"]

EXCLUDED_COLUMNS = [
    "nameOrig",
    "nameDest",
    "isFlaggedFraud",
    TIME_COLUMN,
]