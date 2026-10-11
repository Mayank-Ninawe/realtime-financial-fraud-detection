# Deployment Status and Local Demonstration

## Verified local application

The following components were verified locally:

- Python virtual environment with tested project dependencies.
- XGBoost fraud scoring model loaded through FastAPI.
- Streamlit analyst dashboard connected to FastAPI.
- Kafka-compatible local broker running in Docker.
- Kafka producer replaying PaySim transaction events.
- Kafka consumer validating events, calling FastAPI, and persisting scored alerts.
- MLflow, Feast, and Evidently workflows running locally.

## Docker verification

Docker Desktop was installed and verified with:

```powershell
docker run hello-world
```

The Kafka broker was successfully run through Docker Compose and verified with a console producer-consumer message exchange.

## FastAPI container packaging

The repository includes:

- `Dockerfile.api`
- `requirements-api.txt`
- `docker-compose.yml`
- `.dockerignore`

The API container design intentionally uses a minimal runtime dependency file and mounts local trained model and evaluation-report artifacts as read-only volumes:

```text
./models  -> /app/models:ro
./reports -> /app/reports:ro
```

This avoids committing large generated model artifacts to Git.

## Current Docker API build blocker

The API Docker image build was attempted using Docker Desktop and the official Python 3.10 slim image.

The build downloaded standard Python wheels successfully but failed while downloading the large Linux XGBoost wheel. Pip rejected the partially downloaded wheel because its SHA-256 checksum did not match the expected package checksum.

This is treated as a Docker-network/download-integrity blocker. The project does not bypass package integrity verification, use unofficial binaries, or claim a successful API image build.

## Local demonstration alternative

The working demonstration remains reproducible through the local Python environment:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn api.main:app --app-dir . --port 8000
streamlit run dashboard/app.py
```

Kafka is run through Docker Compose:

```powershell
docker compose -f docker-compose.kafka.yml up -d
```

## Minikube status

Minikube deployment is evaluated separately. Kubernetes manifests are included as deployment configuration only after an image is successfully available to the cluster. The project does not claim a running Kubernetes deployment without verified pod health and endpoint testing.

## Minikube installation blocker

Minikube installation was attempted through Windows Package Manager:

```powershell
winget install Kubernetes.minikube
```

The command found Minikube v1.39.0 but failed while downloading the official installer from GitHub:

```text
InternetReadFile() failed.
0x80072ee2 : unknown error
```

This is a network timeout during installer download. It is consistent with the earlier Docker build failure, where pip rejected a partially downloaded XGBoost Linux wheel because its SHA-256 checksum did not match the expected package checksum.

The project therefore records Minikube as blocked by local network/download reliability. Kubernetes configuration and deployment commands are documented, but no Kubernetes deployment is claimed as verified.

## Cleanup commands

```powershell
docker compose down
docker compose -f docker-compose.kafka.yml down
```