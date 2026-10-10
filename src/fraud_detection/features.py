"""Feature engineering for PaySim transactions."""

from __future__ import annotations

import numpy as np
import pandas as pd

from fraud_detection.config import BASE_FEATURES, DERIVED_FEATURES, TARGET_COLUMN


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add transaction-time balance and transaction-type features."""
    result = df.copy()

    result["sender_balance_change"] = (
        result["newbalanceOrig"] - result["oldbalanceOrg"]
    )
    result["receiver_balance_change"] = (
        result["newbalanceDest"] - result["oldbalanceDest"]
    )
    result["amount_to_sender_old_balance"] = np.divide(
        result["amount"],
        result["oldbalanceOrg"],
        out=np.zeros(len(result), dtype=float),
        where=result["oldbalanceOrg"].to_numpy() != 0,
    )
    result["amount_to_receiver_old_balance"] = np.divide(
        result["amount"],
        result["oldbalanceDest"],
        out=np.zeros(len(result), dtype=float),
        where=result["oldbalanceDest"].to_numpy() != 0,
    )
    result["is_transfer_or_cash_out"] = result["type"].isin(
        ["TRANSFER", "CASH_OUT"]
    ).astype(int)

    return result


def get_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Return model features without labels or post-transaction identifiers."""
    features = add_derived_features(df)
    return features[BASE_FEATURES + DERIVED_FEATURES].copy()


def get_target(df: pd.DataFrame) -> pd.Series:
    """Return the fraud label."""
    return df[TARGET_COLUMN].astype(int)
