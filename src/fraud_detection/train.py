"""Train baseline and XGBoost fraud-detection models."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

from fraud_detection.config import (
    CATEGORICAL_FEATURES,
    MODEL_DIR,
    RANDOM_SEED,
    REPORT_DIR,
)
from fraud_detection.data import (
    create_temporal_splits,
    load_raw_data,
    validate_raw_data,
)
from fraud_detection.features import get_feature_matrix, get_target


def build_preprocessor() -> ColumnTransformer:
    """Build preprocessing for categorical and numeric features."""
    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            )
        ],
        remainder="passthrough",
    )


def calculate_scale_pos_weight(y_train: pd.Series) -> float:
    """Calculate XGBoost class weight from training labels only."""
    negative_count = (y_train == 0).sum()
    positive_count = (y_train == 1).sum()
    return float(negative_count / positive_count)


def train_models() -> None:
    """Train baseline and XGBoost models using a temporal split."""
    df = load_raw_data()
    validate_raw_data(df)

    train_df, validation_df, test_df = create_temporal_splits(df)

    X_train = get_feature_matrix(train_df)
    y_train = get_target(train_df)

    X_validation = get_feature_matrix(validation_df)
    y_validation = get_target(validation_df)

    X_test = get_feature_matrix(test_df)
    y_test = get_target(test_df)

    preprocessor = build_preprocessor()

    baseline_model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", DummyClassifier(strategy="stratified", random_state=RANDOM_SEED)),
        ]
    )
    baseline_model.fit(X_train, y_train)
    baseline_scores = baseline_model.predict_proba(X_validation)[:, 1]
    baseline_validation_ap = average_precision_score(y_validation, baseline_scores)

    scale_pos_weight = calculate_scale_pos_weight(y_train)

    xgb_model = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            (
                "classifier",
                XGBClassifier(
                    n_estimators=300,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    scale_pos_weight=scale_pos_weight,
                    eval_metric="aucpr",
                    random_state=RANDOM_SEED,
                    n_jobs=-1,
                    tree_method="hist",
                ),
            ),
        ]
    )
    xgb_model.fit(X_train, y_train)
    xgb_validation_scores = xgb_model.predict_proba(X_validation)[:, 1]
    xgb_validation_ap = average_precision_score(y_validation, xgb_validation_scores)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(baseline_model, MODEL_DIR / "baseline_model.joblib")
    joblib.dump(xgb_model, MODEL_DIR / "xgboost_model.joblib")

    summary = {
        "train_rows": int(len(train_df)),
        "validation_rows": int(len(validation_df)),
        "test_rows": int(len(test_df)),
        "train_fraud_cases": int(y_train.sum()),
        "validation_fraud_cases": int(y_validation.sum()),
        "test_fraud_cases": int(y_test.sum()),
        "scale_pos_weight": scale_pos_weight,
        "baseline_validation_average_precision": float(baseline_validation_ap),
        "xgboost_validation_average_precision": float(xgb_validation_ap),
    }

    with open(REPORT_DIR / "training_summary.json", "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    train_models()