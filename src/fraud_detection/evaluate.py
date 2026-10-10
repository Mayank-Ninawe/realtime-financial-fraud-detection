"""Evaluate trained fraud-detection models and select a threshold."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_recall_curve,
    precision_score,
    recall_score,
)

from fraud_detection.config import (
    MODEL_DIR,
    RANDOM_SEED,
    REPORT_DIR,
)
from fraud_detection.data import create_temporal_splits, load_raw_data, validate_raw_data
from fraud_detection.features import get_feature_matrix, get_target


def select_threshold(
    y_true: pd.Series,
    scores: np.ndarray,
    minimum_precision: float = 0.50,
) -> float:
    """Select the lowest threshold that meets a minimum precision target.

    If no threshold meets the target, return the threshold that maximizes F1.
    """
    precision, recall, thresholds = precision_recall_curve(y_true, scores)

    candidate_indices = np.where(precision[:-1] >= minimum_precision)[0]

    if len(candidate_indices) > 0:
        best_index = candidate_indices[np.argmax(recall[candidate_indices])]
        return float(thresholds[best_index])

    f1_scores = 2 * precision[:-1] * recall[:-1] / np.maximum(
        precision[:-1] + recall[:-1], 1e-12
    )
    best_index = int(np.argmax(f1_scores))
    return float(thresholds[best_index])


def evaluate_model(
    model_path: Path,
    model_name: str,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    threshold: float,
) -> dict:
    """Evaluate a saved model on the untouched test set."""
    model = joblib.load(model_path)
    scores = model.predict_proba(X_test)[:, 1]
    predictions = (scores >= threshold).astype(int)

    average_precision = average_precision_score(y_test, scores)
    precision = precision_score(y_test, predictions, zero_division=0)
    recall = recall_score(y_test, predictions, zero_division=0)
    matrix = confusion_matrix(y_test, predictions)

    metrics = {
        "model": model_name,
        "threshold": threshold,
        "test_average_precision": float(average_precision),
        "test_precision": float(precision),
        "test_recall": float(recall),
        "true_negatives": int(matrix[0, 0]),
        "false_positives": int(matrix[0, 1]),
        "false_negatives": int(matrix[1, 0]),
        "true_positives": int(matrix[1, 1]),
    }

    return metrics, scores, matrix


def run_evaluation() -> None:
    """Evaluate baseline and XGBoost models on the test set."""
    df = load_raw_data()
    validate_raw_data(df)

    _, validation_df, test_df = create_temporal_splits(df)

    X_validation = get_feature_matrix(validation_df)
    y_validation = get_target(validation_df)

    X_test = get_feature_matrix(test_df)
    y_test = get_target(test_df)

    baseline_model = joblib.load(MODEL_DIR / "baseline_model.joblib")
    xgboost_model = joblib.load(MODEL_DIR / "xgboost_model.joblib")

    baseline_validation_scores = baseline_model.predict_proba(X_validation)[:, 1]
    xgboost_validation_scores = xgboost_model.predict_proba(X_validation)[:, 1]

    baseline_threshold = select_threshold(y_validation, baseline_validation_scores)
    xgboost_threshold = select_threshold(y_validation, xgboost_validation_scores)

    baseline_metrics, _, baseline_matrix = evaluate_model(
        MODEL_DIR / "baseline_model.joblib",
        "baseline",
        X_test,
        y_test,
        baseline_threshold,
    )

    xgboost_metrics, xgboost_test_scores, xgboost_matrix = evaluate_model(
        MODEL_DIR / "xgboost_model.joblib",
        "xgboost",
        X_test,
        y_test,
        xgboost_threshold,
    )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with open(REPORT_DIR / "evaluation_results.json", "w", encoding="utf-8") as file:
        json.dump(
            {
                "baseline": baseline_metrics,
                "xgboost": xgboost_metrics,
            },
            file,
            indent=2,
        )

    precision, recall, _ = precision_recall_curve(y_test, xgboost_test_scores)

    plt.figure(figsize=(8, 5))
    plt.plot(recall, precision, label="XGBoost")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve — XGBoost Test Set")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(REPORT_DIR / "xgboost_precision_recall_curve.png", dpi=150)

    plt.figure(figsize=(5, 4))
    sns.heatmap(
        xgboost_matrix,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["Predicted Legitimate", "Predicted Fraud"],
        yticklabels=["Actual Legitimate", "Actual Fraud"],
    )
    plt.title("XGBoost Confusion Matrix — Test Set")
    plt.tight_layout()
    plt.savefig(REPORT_DIR / "xgboost_confusion_matrix.png", dpi=150)

    print(json.dumps({"baseline": baseline_metrics, "xgboost": xgboost_metrics}, indent=2))


if __name__ == "__main__":
    run_evaluation()