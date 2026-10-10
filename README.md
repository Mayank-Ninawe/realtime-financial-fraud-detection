# Real-Time Financial Fraud Detection Platform

An end-to-end financial fraud detection system built for the AIML-01 internship project at Nexvia Technologies.

## Objective

Build a working platform that:

- Ingests and replays financial transactions.
- Computes fraud-risk features.
- Scores transactions using an XGBoost model.
- Analyzes account relationships and potential fraud rings.
- Exposes predictions through a FastAPI service.
- Streams transactions through Kafka.
- Displays alerts, case information, and analyst feedback in Streamlit.
- Tracks ML experiments with MLflow.
- Monitors data drift with Evidently.
- Demonstrates local deployment with Docker and Minikube.

## Dataset

The initial dataset is **PaySim**, a synthetic mobile-money transaction dataset.

Source: [https://www.kaggle.com/datasets/ealaxi/paysim1](https://www.kaggle.com/datasets/ealaxi/paysim1)

## Current status

- [x] Project planning and requirement tracking
- [ ] GitHub repository setup
- [ ] Local development environment
- [ ] Data acquisition and EDA
- [ ] Baseline model
- [ ] XGBoost model
- [ ] Feature engineering
- [ ] MLflow tracking
- [ ] FastAPI service
- [ ] Streamlit dashboard
- [ ] Kafka streaming
- [ ] Graph-based fraud analysis
- [ ] Feast feature store
- [ ] Drift monitoring
- [ ] Docker and Minikube deployment
- [ ] Final testing and documentation

## Development principles

- Build a simple, reliable end-to-end system first.
- Use only information available at transaction-scoring time.
- Avoid target leakage and future-data leakage.
- Report only measured results.
- Keep datasets, models, logs, and secrets out of Git.