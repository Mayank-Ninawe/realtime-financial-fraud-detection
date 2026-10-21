# System Architecture Refactoring & Verification Record

## Overview

This document details the architectural enhancements, performance optimizations, and integration fixes implemented to transition SentinelGraph from experimental modules into a unified, production-grade fraud detection platform.

---

## 1. Summary of System Refactorings

| Component | Previous State | Refactored State | Impact |
|---|---|---|---|
| **Streaming Persistence** | $O(N^2)$ full JSON list re-write on each event | $O(1)$ append-only JSONL format (`streamed_transactions.jsonl`) | Eliminates disk I/O bottlenecks under high event throughput. |
| **API & Serving** | Isolated `/health` and `/predict` only | Added `/cases`, `/alerts`, `/cases/{id}`, `/graph/summary`, `/metrics/overview`, `/metrics/performance`, with CORS middleware | Enables dynamic, unified frontend and third-party orchestration. |
| **React Frontend** | Hardcoded mock arrays (`ALR-4412`, etc.) & compile-time JSON imports | Real-time FastAPI REST integration with interactive case triage | Fully operational analyst command center. |
| **Feature Store (Feast)** | Unclear architectural purpose & schema disconnect | Explicitly documented as offline/online feature parity validator | Clear MLOps boundaries without latency penalty in live inference. |
| **Repository Hygiene** | Redundant duplicate `artifacts/api/` folder | Deleted duplicate directory | Single source of truth across all API modules. |

---

## 2. Component Specifications

### 2.1 Append-Only Streaming Persistence (`streaming/consumer.py`)

- **Design:** Kafka consumer scores transactions via FastAPI and immediately writes the event payload and decision metadata to disk.
- **Persistence Pattern:** High-performance line-delimited JSON (`.jsonl`).
- **File Paths:**
  - `data/processed/streamed_transactions.jsonl`
  - `data/processed/consumer_errors.jsonl`
- **Complexity:** $O(1)$ constant time append write per event. Backward compatibility supports legacy `.json` list files seamlessly.

### 2.2 FastAPI Endpoints (`api/main.py`)

- `GET /health`: Health status and service identifier.
- `POST /predict`: Real-time transaction scoring via `realtime_safe_xgboost` model pipeline.
- `GET /cases` & `GET /alerts`: Returns live analyst review queue with aggregated count metrics (`open_count`, `resolved_count`, `total_count`).
- `PATCH /cases/{transaction_id}`: Allows analysts to update investigation state (`Under Review`, `Escalated`, `Resolved`) and attach audit feedback.
- `GET /graph/summary`: Graph analytics metrics, connected component counts, and top fraud-linked accounts.
- `GET /metrics/overview`: Aggregated KPI metrics for command center overview.
- `GET /metrics/performance`: Model validation metrics (Precision, Recall, Average Precision, TPR) and full confusion matrix counts.

### 2.3 Feast Feature Store Architecture

- **Registry & Store:** `feature_repo/feature_store.yaml` configuring SQLite online store (`feature_repo/data/online_store.db`).
- **Architectural Boundary:** Feast standardizes feature names and types across training and batch serving pipelines. To maintain sub-10ms real-time latency SLAs, the live scoring service constructs derived features directly from the transaction envelope, while Feast guarantees parity and reproducible definitions.

---

## 3. End-to-End Verification Record

### 3.1 Unit Test Suite (`pytest`)
All 27 test cases across API, streaming, graph features, drift monitoring, and Feast snapshot pass:
```text
tests/test_api.py::test_health_check PASSED
tests/test_api.py::test_predict_valid_transaction PASSED
tests/test_api.py::test_predict_invalid_amount PASSED
tests/test_api.py::test_get_cases_and_alerts PASSED
tests/test_api.py::test_get_graph_summary PASSED
tests/test_api.py::test_get_metrics_overview PASSED
tests/test_api.py::test_get_metrics_performance PASSED
tests/test_drift_monitoring.py::test_prepare_features_returns_expected_columns PASSED
tests/test_drift_monitoring.py::test_controlled_drift_multiplies_amount_only PASSED
tests/test_drift_monitoring.py::test_retraining_review_policy_triggers_for_amount_drift PASSED
tests/test_drift_monitoring.py::test_retraining_review_policy_triggers_for_feature_fraction PASSED
tests/test_drift_monitoring.py::test_retraining_review_policy_does_not_trigger_below_threshold PASSED
tests/test_environment.py::test_pandas_import PASSED
tests/test_environment.py::test_numpy_import PASSED
tests/test_evidently_extraction.py::test_extract_drift_summary_from_evidently_v07_metrics PASSED
tests/test_feast_snapshot.py::test_create_feature_snapshot PASSED
tests/test_features.py::test_add_derived_features PASSED
tests/test_features.py::test_get_realtime_safe_feature_matrix_columns PASSED
tests/test_features.py::test_get_leakage_suspect_feature_matrix_columns PASSED
tests/test_graph_features.py::test_graph_features_do_not_use_same_step_transactions PASSED
tests/test_graph_features.py::test_graph_features_use_only_prior_steps PASSED
tests/test_graph_inspection.py::test_fraud_rate_summary_by_signal PASSED
tests/test_streaming.py::test_validate_event_returns_transaction PASSED
tests/test_streaming.py::test_validate_event_rejects_unsupported_event_type PASSED
tests/test_streaming.py::test_validate_event_rejects_missing_transaction_field PASSED
tests/test_streaming.py::test_json_record_persistence PASSED
tests/test_streaming.py::test_jsonl_record_persistence PASSED
======================= 27 passed, 4 warnings in 23.43s =======================
```

### 3.2 Frontend Build & Browser Verification
- **Build Status:** `npm run build` compiled 2,310 modules cleanly into `frontend/dist/`.
- **Runtime Execution:** Tested via headless browser agent navigating `http://localhost:5173/`.
- **Live User Actions Verified:**
  - Overview metrics accurately loaded from FastAPI `/metrics/overview`.
  - Alerts queue loaded from `/cases`; interactive case resolution dynamically mutated state and persisted audit notes.
  - Roundtrip ping latency measured at **39 ms**.
  - Interactive risk scoring test evaluated sample transaction and rendered model verdict in real time.
