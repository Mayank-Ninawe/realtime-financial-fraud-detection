# SentinelGraph — Real-Time Financial Fraud Detection Platform

SentinelGraph is an end-to-end real-time financial fraud detection platform built on the PaySim transaction dataset. It combines leakage-safe feature engineering, XGBoost-based scoring, FastAPI model serving, Kafka event streaming, a Streamlit analyst dashboard, MLflow experiment tracking, Feast feature-store consistency checks, Evidently drift monitoring, graph-based fraud-ring analysis, and Minikube Kubernetes deployment.

The project demonstrates a complete fraud decision workflow:

```text
Transaction event
→ Kafka ingestion
→ Feature retrieval / construction
→ XGBoost fraud scoring through FastAPI
→ Alert generation and persistence
→ Analyst review in Streamlit
→ Drift monitoring and model governance
```

## Key capabilities

- **Real-time transaction scoring:** FastAPI serves an XGBoost fraud-detection model.
- **Streaming architecture:** Kafka producer replays PaySim transactions; a consumer consumes events, calls the scoring API, and persists alerts.
- **Leakage-safe features:** Historical features use only information available before each transaction.
- **Feature-store consistency:** Feast validates consistency between offline training features and online serving features.
- **Explainable graph analysis:** Account relationships and suspicious connections support fraud-ring feasibility analysis.
- **Analyst dashboard:** Streamlit enables review of scored transactions and alerts.
- **Model governance:** MLflow tracks experiments, parameters, metrics, and model artifacts.
- **Drift monitoring:** Evidently generates data-drift reports and supports review triggers.
- **Containerized deployment:** The API is packaged with Docker and deployed to Minikube Kubernetes.
- **Reproducible workflow:** The repository includes data validation, tests, documentation, and version-controlled implementation phases.

## Architecture

```text
                        ┌────────────────────┐
                        │    PaySim Dataset  │
                        └─────────┬──────────┘
                                  │
                                  ▼
                        ┌────────────────────┐
                        │  Data Validation   │
                        │  and Preprocessing │
                        └─────────┬──────────┘
                                  │
                                  ▼
                        ┌────────────────────┐
                        │ Leakage-safe       │
                        │ Feature Engineering│
                        └─────────┬──────────┘
                                  │
                                  ▼
                        ┌────────────────────┐
                        │   XGBoost Model    │
                        └─────────┬──────────┘
                                  │
                                  ▼
┌──────────────────┐    ┌────────────────────┐    ┌────────────────────┐
│ Kafka Producer   │───▶│    Kafka Broker    │───▶│  Kafka Consumer    │
└──────────────────┘    └────────────────────┘    └─────────┬──────────┘
                                                            │
                                                            ▼
                                                  ┌────────────────────┐
                                                  │  FastAPI Scoring   │
                                                  │        API         │
                                                  └─────────┬──────────┘
                                                            │
                                                            ▼
                                                  ┌────────────────────┐
                                                  │  Alert Persistence │
                                                  └─────────┬──────────┘
                                                            │
                                                            ▼
                                                  ┌────────────────────┐
                                                  │ Streamlit Dashboard│
                                                  └────────────────────┘
```

Supporting MLOps components:

```text
Feast Feature Store → Consistent offline/online features
MLflow → Experiment tracking and model artifacts
Evidently → Data-drift monitoring and review trigger
Docker → API and Kafka containerization
Minikube → Local Kubernetes deployment of the API
```

## Dataset

The project uses the [PaySim Synthetic Financial Dataset](https://www.kaggle.com/datasets/ealaxi/paysim1).

| Metric | Value |
|---|---|
| Source rows | 6,362,620 |
| Preserved processed rows | 6,362,620 |
| Fraud transactions | 8,213 |
| Non-fraud transactions | 6,354,407 |
| Fraud rate | Approximately 0.129% |
| Simulation duration | Approximately 30 days of hourly steps |

The ingestion adapter preserves all source rows and fraud labels. A preprocessing issue that initially removed 16 zero-amount fraudulent transactions was identified and corrected.

## Technology stack

| Layer | Technology |
|---|---|
| Language | Python |
| Data processing | Pandas, NumPy |
| Machine learning | XGBoost, scikit-learn |
| Feature store | Feast |
| Model tracking | MLflow |
| Drift monitoring | Evidently |
| API | FastAPI, Uvicorn |
| Streaming | Apache Kafka |
| Dashboard | Streamlit |
| Graph analysis | NetworkX-based feasibility workflow |
| Containers | Docker, Docker Compose |
| Kubernetes | Minikube, kubectl |
| Quality tools | Pytest, Ruff |
| Version control | Git, GitHub |

## Repository structure

```text
realtime-financial-fraud-detection/
├── api/
│   ├── main.py
│   ├── predictor.py
│   ├── schemas.py
│   └── __init__.py
├── dashboard/
│   └── app.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample/
├── docs/
│   ├── project_plan.md
│   ├── graph_feasibility.md
│   └── deployment_status.md
├── feature_repo/
│   └── ...
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   └── public/
├── k8s/
│   ├── fraud-api-deployment.yaml
│   └── fraud-api-service.yaml
├── models/
├── notebooks/
│   └── 01_eda.ipynb
├── reports/
├── scripts/
│   ├── adapters/
│   └── ...
├── src/
├── streaming/
├── tests/
├── .dockerignore
├── .gitignore
├── docker-compose.yml
├── docker-compose.kafka.yml
├── Dockerfile.api
├── README.md
├── requirements.txt
└── .venv/
```

Large generated artifacts such as raw data, processed Parquet files, trained models, MLflow runs, and monitoring reports are excluded from Git through `.gitignore`.

## Frontend dashboard

A React + TypeScript + Vite dashboard lives in the `frontend/` directory and serves as the primary demo interface for the fraud-monitoring experience. It is designed to work with the existing FastAPI service and exposes the real `/health` and `/predict` behavior without replacing the backend or ML pipeline.

### Run frontend locally

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

### Frontend stack

- React
- TypeScript
- Vite
- Tailwind CSS
- Recharts
- shadcn/ui-inspired component primitives

### Backend integration

The frontend calls the existing Python backend endpoints:

- `GET /health` for service status
- `POST /predict` with a transaction payload to score a transaction

The legacy Streamlit dashboard remains available as a fallback and is intentionally preserved.

## Core workflow

### 1. Data ingestion and validation

The PaySim adapter normalizes raw transactions into a consistent schema:

```text
transaction_id
event_time
sender_id
receiver_id
transaction_type
amount
is_fraud
```

It validates row preservation, fraud-label preservation, duplicate handling, chronological ordering, and required fields.

### 2. Leakage-safe feature engineering

Features are computed using only information available before the transaction being scored.

For a transaction at time \(T\):

```text
Allowed: transactions with event_time < T
Excluded: current transaction and all future transactions
```

This prevents future-data leakage and makes the workflow more realistic for production fraud detection.

### 3. Model training

An XGBoost classifier is trained on engineered features. Because the dataset is highly imbalanced, evaluation focuses on fraud-relevant metrics rather than accuracy alone.

Typical evaluation metrics include:

- Precision
- Recall
- F1-score
- PR-AUC
- ROC-AUC
- Precision at top-k alerts

### 4. FastAPI serving

FastAPI loads the trained model and exposes scoring and health endpoints.

Example health response:

```json
{
  "status": "healthy",
  "service": "fraud-detection-api"
}
```

### 5. Kafka streaming

The producer replays PaySim transactions to a Kafka topic. The consumer reads each event, calls the FastAPI scoring endpoint, and persists the resulting alert or scored transaction.

```text
Kafka producer → Kafka topic → Kafka consumer → FastAPI → Alert store
```

### 6. Analyst dashboard

The Streamlit dashboard connects to the FastAPI service and allows analysts to inspect scored transactions, fraud probabilities, and alerts.

### 7. Monitoring and governance

MLflow records experiment metadata and model artifacts. Evidently monitors input-data drift and generates reports that can trigger model review.

## Local setup

### Prerequisites

- Python 3.10+
- Git
- Docker Desktop
- Minikube
- kubectl

### Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Run tests and linting

```powershell
pytest
ruff check .
```

## Running the API locally

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn api.main:app --app-dir . --port 8000
```

Open:

```text
http://127.0.0.1:8000/docs
```

Health check:

```powershell
curl.exe http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "fraud-detection-api"
}
```

## Running the dashboard

From the repository root (`D:\Nexvia-Internship\realtime-financial-fraud-detection`),
start the API first in one PowerShell terminal:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "$PWD\src"
uvicorn api.main:app --app-dir . --host 127.0.0.1 --port 8000
```

In a second PowerShell terminal, also from the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run dashboard\app.py
```

Open the URL shown by Streamlit, usually:

```text
http://127.0.0.1:8501
```

The dashboard checks `/health` and then performs a model-backed readiness
prediction. “API reachable” is therefore kept distinct from “model loaded and
prediction ready.” The Overview page labels PaySim `isFraud` counts as
historical data, while the Fraud alerts page only displays locally persisted
Kafka consumer records. Case status updates are local JSON records in
`data\processed\cases.json`; they are not an external case-management system.

The dashboard can be explored without Kafka. If Kafka is not running, it
shows “Streaming unavailable” and keeps historical analysis and verified API
scoring available.

## Running Kafka streaming

Start the Kafka broker:

```powershell
docker compose -f docker-compose.kafka.yml up -d
```

Run the producer and consumer using the project’s streaming scripts.

Stop Kafka when finished:

```powershell
docker compose -f docker-compose.kafka.yml down
```

## Docker API build

Build the API image:

```powershell
docker compose build --no-cache fraud-api
```

Successful build result:

```text
✔ Image realtime-financial-fraud-detection-fraud-api Built
```

The API image includes only the runtime dependencies and source code needed for serving.

## Kubernetes deployment

### Start Minikube

```powershell
$env:MINIKUBE_HOME = "D:\minikube-home"
minikube start --driver=docker
```

Verify the cluster:

```powershell
minikube status
kubectl get nodes
```

Expected node status:

```text
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   ...   v1.37.0
```

### Load the API image

```powershell
minikube image load realtime-financial-fraud-detection-fraud-api:latest
```

### Deploy the API

```powershell
kubectl apply -f k8s/fraud-api-deployment.yaml
kubectl apply -f k8s/fraud-api-service.yaml
```

### Verify deployment

```powershell
kubectl get pods -l app=fraud-api
kubectl get svc fraud-api
kubectl logs -l app=fraud-api --tail=100
```

Expected pod status:

```text
NAME                         READY   STATUS    RESTARTS   AGE
fraud-api-77cf7f7cdb-shcqx   1/1     Running   0          ...
```

### Access the API locally

```powershell
minikube service fraud-api --url
```

Then test:

```powershell
curl.exe http://127.0.0.1:63861/health
```

Expected:

```json
{
  "status": "healthy",
  "service": "fraud-detection-api"
}
```

## Deployment verification

The following deployment milestones were verified:

| Component | Status |
|---|---|
| Docker Desktop | Verified |
| Kafka in Docker Compose | Verified |
| FastAPI Docker image | Built successfully |
| Minikube installation | Complete |
| Minikube cluster | Running and Ready |
| Kubernetes Deployment | Created |
| Kubernetes Service | Created |
| API pod | `1/1 Running` |
| Readiness probe | Passing |
| `/health` endpoint | HTTP 200 |
| Kubernetes API deployment | Verified complete |

## Graph feasibility

The project evaluates whether account-relationship graphs can improve fraud detection by identifying suspicious connections and potential fraud rings.

Graph nodes include sender and receiver accounts, while transactions connect them. Temporal graph features use only prior transactions, preserving the leakage-safety rule.

Example graph relationship:

```text
Account A → Transaction → Account B
Account B → Transaction → Account C
Account C → Transaction → Account D
```

If multiple connected accounts participate in suspicious or fraud-labeled transactions, the connected component may indicate coordinated fraud behavior.

See [`docs/graph_feasibility.md`](docs/graph_feasibility.md) for the full feasibility assessment.

## MLOps workflow

### MLflow

MLflow is used to track:

- Experiment parameters
- Evaluation metrics
- Model artifacts
- Model versions
- Training metadata

### Evidently

Evidently is used to monitor:

- Feature distribution drift
- Data-quality changes
- Input-data stability
- Review triggers for model retraining or investigation

### Feast

Feast is used to maintain consistency between:

- Offline features used for training
- Online features used during serving

## Project documentation

- [`docs/project_plan.md`](docs/project_plan.md) — Full phased implementation plan and completion status.
- [`docs/graph_feasibility.md`](docs/graph_feasibility.md) — Graph-based fraud-ring analysis and feasibility assessment.
- [`docs/deployment_status.md`](docs/deployment_status.md) — Docker, Kafka, Minikube, and Kubernetes deployment verification.

## Cleanup

Stop Kubernetes resources:

```powershell
kubectl delete -f k8s/fraud-api-service.yaml
kubectl delete -f k8s/fraud-api-deployment.yaml
minikube stop
```

Stop Kafka:

```powershell
docker compose -f docker-compose.kafka.yml down
```

## Future improvements

- Deploy Kafka inside Kubernetes using StatefulSets and persistent volumes.
- Add production-grade secrets management.
- Add horizontal pod autoscaling.
- Add CI/CD pipelines for tests, linting, Docker builds, and deployments.
- Benchmark p95 prediction latency under concurrent traffic.
- Implement a complete analyst-feedback retraining loop.
- Extend graph analysis into a scheduled fraud-ring detection service.
- Add Prometheus and Grafana-based operational monitoring.

## Professional summary

SentinelGraph demonstrates a production-oriented fraud detection workflow: validated PaySim data is transformed into leakage-safe features, scored by an XGBoost model through FastAPI, streamed through Kafka, reviewed through Streamlit, monitored with Evidently, tracked with MLflow, and deployed to Minikube Kubernetes.

The project emphasizes reproducibility, data integrity, explainability, and deployment verification rather than presenting an isolated machine-learning notebook.