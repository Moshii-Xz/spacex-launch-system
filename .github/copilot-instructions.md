# Copilot Instructions — SpaceX Launch System

## Architecture Overview

```
SpaceX API (v4) → Lambda (Python) ──upsert──► DynamoDB
                       ↑                          ↓
               EventBridge (6h) /       FastAPI Backend (ECS Fargate)
               API Gateway (manual)              ↓
                                     ALB (single stable entry point)
                                               ↓
                                      React/Vite WebApp (ECS Fargate)
```

- **Lambda** (`lambda/`) is the sole writer to DynamoDB. It fetches past + upcoming launches from `https://api.spacexdata.com/v4` and upserts them.
- **FastAPI backend** (`backend/`) is read-only against DynamoDB; it never writes. It exposes `POST /api/v1/trigger` which invokes the Lambda synchronously via boto3.
- **WebApp** (`webapp/`) only calls the FastAPI backend; it never talks to DynamoDB or SpaceX API directly.
- **ALB routing**: `/*` → WebApp (nginx, port 80); `/api/v1/*`, `/docs`, `/redoc`, `/openapi.json` → Backend (port 8000).
- All AWS resource names follow the pattern `{name}-{environment}` (e.g., `spacex-launches-dev`, `spacex-data-collector-dev`).

## DynamoDB Schema

Table: `spacex-launches-{env}` | PK: `launch_id` (String)

GSIs:
- `status-index` — PK: `status` (`success` | `failed` | `upcoming` | `unknown`)
- `launch_date-index` — PK: `launch_date` (ISO 8601 UTC string)

## Import Conventions

- **Backend**: always use the package prefix — `from backend.models.launch import Launch`, `from backend.services.dynamo_service import DynamoService`.
- **Lambda**: flat imports, no package — `from spacex_client import SpaceXClient`, `from dynamo_repository import DynamoRepository`. Lambda files live at the root of `lambda/`.

## Local Development

```bash
# Start DynamoDB local (8000), FastAPI backend (8080), and React dev server (3000)
docker-compose up

# Backend Swagger available at http://localhost:8080/docs
# WebApp at http://localhost:3000
```

Environment variables needed locally (already set in docker-compose):
- `DYNAMODB_ENDPOINT=http://dynamodb-local:8000` — enables DynamoDB-local mode in both backend and lambda.
- `VITE_API_BASE_URL=http://localhost:8080/api/v1` — points webapp at the backend.

## Running Tests

```bash
# Lambda tests (pytest + moto for AWS mocking)
cd lambda
pip install -r requirements-dev.txt
pytest tests/ -v --cov=. --cov-report=term-missing

# Backend tests — run from project root, NOT from backend/
pip install -r backend/requirements-dev.txt
pytest backend/tests/ -v

# WebApp tests (vitest)
cd webapp
npm install
npm run test          # watch mode
npm run test -- --run  # single run (CI)
```

Backend tests must set AWS env vars before importing `backend.main` — see the pattern in [backend/tests/test_api.py](backend/tests/test_api.py#L8). Running `pytest` from inside `backend/` breaks the `backend.*` imports; always run from the project root.

## Key Patterns

- **Status resolution**: determined in `lambda/handler.py::_resolve_status()` — `upcoming=True` → `"upcoming"`, `success=True` → `"success"`, `success=False` → `"failed"`, else `"unknown"`.
- **DynamoDB access**: backend uses `DynamoService` (read-only); lambda uses `DynamoRepository` (upsert). They are parallel implementations — do not mix them.
- **DynamoDB local detection**: both services check for `DYNAMODB_ENDPOINT` env var and pass it as `endpoint_url` to boto3 when set.
- **CORS**: controlled via `CORS_ORIGINS` env var (comma-separated list), defaults to `"*"`.

## Infrastructure (Terraform)

All infra is in `infra/`. State is stored locally (`terraform.tfstate`). Default environment is `dev`, region `us-east-1`.

```bash
cd infra
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

After apply, get URLs with:
```bash
terraform -chdir=infra output api_gateway_url   # manual Lambda trigger endpoint
terraform -chdir=infra output webapp_url         # ALB DNS (stable, use this for the app)
```

## CI/CD Pipeline (GitHub Actions)

Defined in `.github/workflows/deploy.yml`. Triggers on push/PR to `main`. Jobs run in order:
1. `test-lambda` — pytest with coverage, uploads to Codecov
2. `test-backend` — pytest with coverage (env vars injected via `env:` block, not os.environ)
3. `test-webapp` — vitest + production build
4. `build-push-webapp` / `build-push-backend` — Docker build + ECR push (requires `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` secrets)
5. `deploy-ecs` — `aws ecs update-service --force-new-deployment` for both services
6. `deploy-lambda` — zips `lambda/*.py` + `lambda/package/` and calls `aws lambda update-function-code`

ECS service names: `spacex-webapp-service-dev`, `spacex-backend-service-dev` — cluster `spacex-cluster-dev`.

## Lambda Deployment

```bash
cd lambda
pip install -r requirements.txt -t ./package
cd package && zip -r ../dist/function.zip . && cd ..
zip -g dist/function.zip *.py
aws lambda update-function-code \
  --function-name spacex-data-collector-dev \
  --zip-file fileb://dist/function.zip
```
