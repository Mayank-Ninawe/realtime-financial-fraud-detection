# SentinelGraph

SentinelGraph is a local, end-to-end fraud detection application built around the PaySim synthetic transaction dataset. It trains a leakage-aware XGBoost model, exposes model-backed scoring through FastAPI, persists scored cases, and provides React and Streamlit analyst interfaces.

The repository contains the application code and reproducibility tooling. The PaySim CSV, trained models, reports, databases, and other runtime outputs are intentionally excluded from Git.

## What is implemented

- **Model pipeline:** CSV validation, chronological train/validation/test splits, derived transaction features, XGBoost training, evaluation, and MLflow tracking.
- **Realtime scoring:** FastAPI endpoints for health, readiness, prediction, cases, metrics, and graph summaries.
- **Persistence:** SQLite for local development; PostgreSQL is supported through SQLAlchemy and Docker Compose.
- **Analyst interfaces:** React/Vite dashboard for the main application and a Streamlit dashboard for operational review.
- **Streaming:** Kafka producer and consumer for replaying PaySim transactions and sending events to the scoring API.
- **Monitoring and analysis:** Evidently drift reports, Feast feature snapshots, and NetworkX account-relationship analysis.
- **Deployment:** Docker Compose files for PostgreSQL/Kafka and Kubernetes manifests for the API.
- **Verification:** Pytest, Ruff, frontend TypeScript/Vite build, Playwright configuration, and GitHub Actions CI.

## Architecture

```text
PaySim CSV
   |
   +--> training/evaluation --> models/ and reports/
   |
   +--> Kafka producer --> Kafka --> consumer --> FastAPI /predict
                                                   |
                                                   +--> local database
                                                   +--> React dashboard
                                                   +--> Streamlit dashboard
```

The deployed model is `realtime_safe_xgboost`. Its feature set uses transaction type, amount, pre-transaction balances, and derived pre-transaction indicators. Post-transaction balance fields are used only by the diagnostic `leakage_suspect_xgboost` experiment and are not used by the primary scoring path.

## Repository layout

```text
backend/
  api/                 FastAPI application, schemas, and predictor
  dashboard/           Streamlit analyst dashboard
  feature_store/       Feast repository and snapshot generation
  graph/               Account graph construction and inspection
  monitoring/          Evidently drift report generation
  persistence/         SQLAlchemy database layer
  src/fraud_detection/ Data loading, features, training, and evaluation
  streaming/           Kafka producer and consumer
  tests/               Backend tests
frontend/              React + TypeScript + Vite dashboard
infra/docker/          API, PostgreSQL, and Kafka Compose definitions
infra/k8s/             Kubernetes API manifests
data/                  Local dataset and generated transaction data
models/                Local trained model artifacts
reports/               Local evaluation and training outputs
```

## Requirements

- Python 3.10
- Node.js 20 and npm
- The PaySim dataset
- Docker Desktop, if PostgreSQL, Kafka, or the containerized API is required

Create the virtual environment and install Python dependencies:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Install frontend dependencies:

```powershell
cd frontend
npm ci
cd ..
```

## Dataset and generated artifacts

Download `PS_20174392719_1491204439457_log.csv` from the PaySim dataset and place it at:

```text
data/raw/PS_20174392719_1491204439457_log.csv
```

The code validates the required PaySim columns before training. Do not commit the CSV, model binaries, MLflow database/artifacts, generated reports, or local application database.

The current local evaluation artifact records the following for the realtime-safe model:

| Metric | Value |
|---|---:|
| Test average precision | 0.9926426882 |
| Test precision | 0.4553283100 |
| Test recall | 1.0000000000 |
| Test F2 score | 0.8069439145 |
| Test alert rate | 0.0269869858 |
| Test false-positive rate | 0.0148819152 |

These values describe the checked-in code and local generated report, not a production performance guarantee.

## Run locally

### FastAPI backend

From the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "$PWD\backend\src;$PWD\backend"
python -m uvicorn api.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Health and readiness:

```powershell
curl.exe http://127.0.0.1:8000/health
curl.exe http://127.0.0.1:8000/readyz
```

OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

### React frontend

In a second terminal:

```powershell
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api/*` to the FastAPI service on port 8000.

### Streamlit dashboard

In another terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python -m streamlit run backend\dashboard\app.py --server.address 127.0.0.1 --server.port 8501
```

Open `http://127.0.0.1:8501`. The dashboard can be used without Kafka, but the API must be running.

## Train and evaluate

With the dataset in place:

```powershell
$env:PYTHONPATH = "$PWD\backend\src;$PWD\backend"
python -m fraud_detection.train
python -m fraud_detection.evaluate
```

Training writes model files to `models/` and a summary to `reports/training_summary.json`. Evaluation writes metrics and plots to `reports/`. MLflow uses the local `mlflow.db` tracking database and `mlartifacts/`.

## Kafka workflow

Start Kafka:

```powershell
docker compose -f infra\docker\docker-compose.kafka.yml up -d
```

Start the producer and consumer from separate terminals after starting the API:

```powershell
$env:PYTHONPATH = "$PWD\backend\src;$PWD\backend"
python -m streaming.producer
```

```powershell
$env:PYTHONPATH = "$PWD\backend\src;$PWD\backend"
python -m streaming.consumer
```

The producer replays the PaySim input to Kafka. The consumer calls `/predict` and persists scored events. Kafka-generated JSONL files and the local database remain ignored.

## Docker Compose

For the API with PostgreSQL, copy `.env.example` to `.env`, replace the placeholder values, and run:

```powershell
Copy-Item .env.example .env
docker compose --env-file .env -f infra\docker\docker-compose.yml up --build
```

The API is exposed on port 8000. The container expects model files and `reports/evaluation_results.json` to exist locally before it is built.

## Verification

```powershell
$env:PYTHONPATH = "$PWD\backend\src;$PWD\backend"
ruff check backend
pytest -q
```

Build the frontend:

```powershell
cd frontend
npm ci
npm run build
```

CI runs the backend lint/tests, the frontend build, and Docker Compose configuration validation on pushes to `main`/`master` and on pull requests.

## Configuration

`.env.example` documents local configuration:

- `POSTGRES_PASSWORD`: PostgreSQL password for Compose.
- `CORS_ALLOWED_ORIGINS`: comma-separated frontend origins.
- `API_KEY`: optional API key enforced by the FastAPI middleware when set.
- `PREDICT_RETRY_COUNT`: Kafka consumer retry count for prediction requests.

Do not commit `.env` or real credentials.
