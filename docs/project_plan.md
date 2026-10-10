# Project Plan — AIML-01

## Project

**Real-Time Financial Fraud Detection Platform**

## Primary dataset

PaySim synthetic mobile-money transaction dataset.

Source: https://www.kaggle.com/datasets/ealaxi/paysim1

## Initial dataset decision

PaySim is selected as the starting dataset because it provides sender and receiver account identifiers, transaction types, amounts, simulation time steps, and fraud labels. These fields support transaction replay, account-relationship analysis, velocity features, and an initial fraud-detection model.

## Known dataset limitations

- PaySim is synthetic, not real customer transaction data.
- It does not contain genuine device, IP address, geolocation, or merchant identity fields.
- Device or location features must not be invented.
- Post-transaction balance fields require careful leakage analysis.
- Fraud labels are concentrated in certain transaction types; this must be validated during EDA.

## Development phases

1. Repository and environment setup
2. Initial repository structure
3. PaySim acquisition and EDA
4. Baseline model and XGBoost training
5. Feature engineering and MLflow
6. FastAPI and Streamlit application
7. Kafka transaction replay
8. Account graph and graph-based risk signals
9. Feast feature store
10. Evidently drift monitoring
11. Docker and Minikube deployment
12. Final testing, documentation, and presentation

## Current status

- Repository created.
- Python virtual environment created.
- Initial data-science dependencies installed.
- Jupyter kernel registered.
- Initial project structure being established.
