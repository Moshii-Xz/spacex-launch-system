# SpaceX Launch System

Sistema fullstack en AWS que recolecta, almacena y visualiza datos de lanzamientos espaciales de SpaceX, desplegado mediante infraestructura como código (Terraform) y automatizado con un pipeline CI/CD en GitHub Actions.

---

## Índice

1. [Arquitectura](#arquitectura)
2. [Componentes](#componentes)
3. [Base de datos — DynamoDB](#base-de-datos--dynamodb)
4. [Estructura del proyecto](#estructura-del-proyecto)
5. [Requisitos previos](#requisitos-previos)
6. [Despliegue desde cero](#despliegue-desde-cero)
7. [Desarrollo local](#desarrollo-local)
8. [Pruebas automatizadas](#pruebas-automatizadas)
9. [Pipeline CI/CD](#pipeline-cicd)
10. [API REST — Referencia de endpoints](#api-rest--referencia-de-endpoints)
11. [URLs públicas](#urls-públicas)
12. [Cómo extender el sistema](#cómo-extender-el-sistema)

---

## Arquitectura

```
SpaceX API (v4)
      │
      ▼
Lambda Python ──── upsert ────► DynamoDB
      ▲                              │
      │                              │ lectura
EventBridge (cada 6h)        FastAPI Backend
API Gateway (manual)               (ECS Fargate)
                                      │
                              Application Load Balancer
                               (DNS estable, puerto 80)
                                      │
                             ┌────────┴─────────┐
                         /api/v1/*            /*
                        /docs, /redoc     React WebApp
                       FastAPI Backend    (ECS Fargate,
                       (ECS Fargate,        nginx)
                        puerto 8000)
```

**Flujo de datos:**

1. **EventBridge** dispara la Lambda cada 6 horas (o invocación manual vía API Gateway / `POST /api/v1/trigger`).
2. La **Lambda** consume `https://api.spacexdata.com/v4/launches/past` y `/launches/upcoming`, luego hace upsert a DynamoDB.
3. El **Backend FastAPI** expone una API REST de solo lectura sobre DynamoDB.
4. La **WebApp React** consume únicamente el Backend; nunca accede directo a DynamoDB ni a SpaceX.
5. El **ALB** enruta: `/*` → WebApp (nginx) y `/api/v1/*`, `/docs`, `/redoc`, `/openapi.json` → Backend.

---

## Componentes

### Lambda (`lambda/`)

- Escrita en Python 3.11.
- `SpaceXClient` — cliente HTTP para la API pública de SpaceX v4 (`spacex_client.py`).
- `DynamoRepository` — upsert a DynamoDB; verifica existencia antes de insertar o actualizar (`dynamo_repository.py`).
- `handler.py::lambda_handler` — punto de entrada; compatible con EventBridge y API Gateway (detecta `requestContext`/`httpMethod` en el evento).
- `_resolve_status()` determina el estado: `upcoming=True` → `"upcoming"`, `success=True` → `"success"`, `success=False` → `"failed"`, else `"unknown"`.
- **Es el único componente con permisos de escritura sobre DynamoDB.**

### Backend FastAPI (`backend/`)

- Python 3.11 + FastAPI + Pydantic v2.
- Solo lectura sobre DynamoDB via `DynamoService` (`backend/services/dynamo_service.py`).
- Importaciones siempre con prefijo de paquete: `from backend.models.launch import Launch`.
- CORS configurable via variable de entorno `CORS_ORIGINS` (lista separada por comas, defecto `"*"`).

### WebApp React (`webapp/`)

- React 18 + TypeScript + Vite.
- Servida por nginx en producción (puerto 80).
- Comunica exclusivamente con el Backend a través de `VITE_API_BASE_URL`.
- Pruebas con Vitest.

### Infraestructura (`infra/`)

- 100% Terraform (>= 1.5). Estado local en `terraform.tfstate`.
- Recursos: DynamoDB, Lambda, API Gateway v2, ECR (x2), ECS Cluster, ALB, Target Groups, Security Groups, IAM.
- Variables en `variables.tf`; entorno por defecto `dev`, región `us-east-1`.
- Convención de nombres: `{nombre}-{entorno}` — p.ej. `spacex-launches-dev`, `spacex-cluster-dev`.

---

## Base de datos — DynamoDB

**Tabla:** `spacex-launches-{env}`

| Atributo | Tipo | Rol |
|---|---|---|
| `launch_id` | String | Clave primaria (PK) |
| `mission_name` | String | Nombre de la misión |
| `rocket_name` | String | Nombre del cohete |
| `launch_date` | String | ISO 8601 UTC |
| `status` | String | `success` \| `failed` \| `upcoming` \| `unknown` |
| `launchpad` | String | Plataforma de lanzamiento |
| `flight_number` | String | Número de vuelo |
| `details` | String | Descripción |
| `payloads` | List | IDs de cargas útiles |
| `webcast_url` | String | YouTube / webcast |
| `article_url` | String | Artículo de prensa |
| `wikipedia_url` | String | Wikipedia |
| `patch_small` / `patch_large` | String | URLs del parche de la misión |

**Índices secundarios globales (GSI):**

| GSI | PK | Uso |
|---|---|---|
| `status-index` | `status` | Filtrar por estado |
| `launch_date-index` | `launch_date` | Ordenar/filtrar por fecha |

Billing mode: `PAY_PER_REQUEST`.

---

## Estructura del proyecto

```
spacex-launch-system/
├── .github/
│   ├── workflows/
│   │   └── deploy.yml          # Pipeline CI/CD (7 jobs)
│   └── copilot-instructions.md # Instrucciones para agentes de IA
├── infra/                      # Infraestructura como código (Terraform)
│   ├── main.tf                 # Provider y DynamoDB
│   ├── lambda.tf               # Lambda + EventBridge + API Gateway
│   ├── ecs.tf                  # ECR, ECS, ALB, Security Groups
│   ├── iam.tf                  # Roles y políticas IAM
│   ├── variables.tf
│   └── outputs.tf
├── lambda/                     # Función AWS Lambda
│   ├── handler.py              # Punto de entrada
│   ├── spacex_client.py        # Cliente HTTP SpaceX API
│   ├── dynamo_repository.py    # Capa de acceso a DynamoDB (upsert)
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── package/                # Dependencias empaquetadas para deploy
│   └── tests/                  # pytest + moto
├── backend/                    # API REST FastAPI
│   ├── main.py
│   ├── models/launch.py        # Pydantic models
│   ├── routers/                # launches.py | sync.py | health.py
│   ├── services/dynamo_service.py  # Capa de lectura DynamoDB
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── tests/test_api.py
├── webapp/                     # Frontend React + Vite
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/launchService.ts
│   │   └── types/
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml          # Entorno de desarrollo local completo
└── README.md
```

---

## Requisitos previos

| Herramienta | Versión mínima |
|---|---|
| [AWS CLI v2](https://aws.amazon.com/cli/) | 2.x |
| [Terraform](https://terraform.io) | >= 1.5 |
| [Python](https://python.org) | 3.11+ |
| [Node.js](https://nodejs.org) | 20+ |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | cualquiera reciente |

---

## Despliegue desde cero

### 1. Clonar el repositorio y configurar AWS CLI

```bash
git clone https://github.com/Moshii-Xz/spacex-launch-system.git
cd spacex-launch-system

aws configure
# AWS Access Key ID:     <tu_key>
# AWS Secret Access Key: <tu_secret>
# Default region:        us-east-1
# Default output format: json
```

### 2. Desplegar toda la infraestructura con Terraform

Esto crea DynamoDB, Lambda, EventBridge, API Gateway, ECR, ECS Cluster, ALB, IAM roles y Security Groups.

```bash
cd infra
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

Al finalizar, Terraform imprime todas las URLs:

```bash
terraform output webapp_url        # URL pública de la WebApp
terraform output swagger_url       # URL del Swagger UI
terraform output api_gateway_url   # Endpoint para disparar la Lambda manualmente
```

### 3. Construir y publicar las imágenes Docker en ECR

Obtén los repositorios ECR:

```bash
terraform output ecr_repository_url        # ECR WebApp
terraform output ecr_backend_repository_url # ECR Backend
```

```bash
# Login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account_id>.dkr.ecr.us-east-1.amazonaws.com

# Backend
cd backend
docker build -t spacex-backend-dev .
docker tag spacex-backend-dev:latest <ecr_backend_url>:latest
docker push <ecr_backend_url>:latest

# WebApp
cd ../webapp
docker build -t spacex-webapp-dev .
docker tag spacex-webapp-dev:latest <ecr_webapp_url>:latest
docker push <ecr_webapp_url>:latest
```

### 4. Actualizar los servicios ECS

```bash
# Backend
aws ecs update-service \
  --cluster spacex-cluster-dev \
  --service spacex-backend-service-dev \
  --force-new-deployment

# WebApp
aws ecs update-service \
  --cluster spacex-cluster-dev \
  --service spacex-webapp-service-dev \
  --force-new-deployment
```

### 5. Desplegar la Lambda manualmente

```bash
cd lambda
pip install -r requirements.txt -t ./package
mkdir -p dist
cd package && zip -r ../dist/function.zip . && cd ..
zip -g dist/function.zip *.py

aws lambda update-function-code \
  --function-name spacex-data-collector-dev \
  --zip-file fileb://dist/function.zip
```

### 6. Verificar el despliegue

```bash
# Health check del Backend
curl http://spacex-alb-dev-1388470716.us-east-1.elb.amazonaws.com/health

# Disparar sincronización manual
curl -X POST https://z7i0z19trh.execute-api.us-east-1.amazonaws.com/dev/trigger

# Listar lanzamientos
curl http://spacex-alb-dev-1388470716.us-east-1.elb.amazonaws.com/api/v1/launches?limit=5
```

---

## Desarrollo local

`docker-compose up` levanta tres servicios: DynamoDB local (puerto 8000), Backend FastAPI (puerto 8080) y WebApp React en modo dev con hot-reload (puerto 3000).

```bash
docker-compose up
```

| Servicio | URL local |
|---|---|
| WebApp | http://localhost:3000 |
| Backend API | http://localhost:8080/api/v1 |
| Swagger UI | http://localhost:8080/docs |
| DynamoDB local | http://localhost:8000 |

Variables de entorno usadas en local (ya configuradas en `docker-compose.yml`):

| Variable | Valor local | Descripción |
|---|---|---|
| `DYNAMODB_ENDPOINT` | `http://dynamodb-local:8000` | Activa modo DynamoDB-local en Backend y Lambda |
| `DYNAMODB_TABLE` | `spacex-launches-dev` | Nombre de la tabla |
| `VITE_API_BASE_URL` | `http://localhost:8080/api/v1` | URL del Backend para la WebApp |
| `CORS_ORIGINS` | `http://localhost:3000` | Orígenes permitidos |

---

## Pruebas automatizadas

### Lambda — pytest + moto (mock de AWS)

```bash
cd lambda
pip install -r requirements-dev.txt
pytest tests/ -v --cov=. --cov-report=term-missing
```

Cobertura de: parsing de la API SpaceX, lógica de upsert en DynamoDB, manejo de errores HTTP y de boto3, resolución de estados.

### Backend — pytest + FastAPI TestClient

> **Importante:** ejecutar siempre desde la raíz del proyecto, no desde `backend/`. Los imports usan el prefijo `backend.*`.

```bash
# Desde la raíz del proyecto
pip install -r backend/requirements-dev.txt
pytest backend/tests/ -v --cov=backend --cov-report=term-missing
```

Las variables de entorno AWS deben definirse **antes** de importar `backend.main` (ver patrón en `backend/tests/test_api.py` líneas 8-13).

### WebApp — Vitest

```bash
cd webapp
npm install
npm run test          # modo watch
npm run test -- --run  # ejecución única (modo CI)
npm run build         # verificar build de producción
```

---

## Pipeline CI/CD

Definido en `.github/workflows/deploy.yml`. Se activa en cada **push o PR a `main`**.

```
push a main
    │
    ├── test-lambda       (pytest + cobertura → Codecov)
    ├── test-backend      (pytest + cobertura → Codecov)
    └── test-webapp       (vitest + build producción)
              │
              ▼  (solo en push, no en PR)
         build-and-push   (Docker build → ECR: webapp + backend)
              │
    ┌─────────┴──────────┐
    ▼                    ▼
deploy-webapp        deploy-backend
(ECS update-service  (ECS update-service
 + wait stable)       + wait stable)

test-lambda ──► deploy-lambda  (zip *.py + package/ → aws lambda update-function-code
                                + wait function-updated)
```

**Cada job de deploy espera estabilización** (`aws ecs wait services-stable` / `aws lambda wait function-updated`) antes de completarse.

### Secrets requeridos en GitHub

| Secret | Descripción |
|---|---|
| `AWS_ACCESS_KEY_ID` | Access key de AWS |
| `AWS_SECRET_ACCESS_KEY` | Secret key de AWS |

### Variables de entorno en el workflow

| Variable | Valor |
|---|---|
| `AWS_REGION` | `us-east-1` |
| `ECR_REPOSITORY_WEBAPP` | `spacex-webapp-dev` |
| `ECR_REPOSITORY_BACKEND` | `spacex-backend-dev` |
| `ECS_CLUSTER` | `spacex-cluster-dev` |
| `ECS_SERVICE_WEBAPP` | `spacex-webapp-service-dev` |
| `ECS_SERVICE_BACKEND` | `spacex-backend-service-dev` |
| `LAMBDA_FUNCTION` | `spacex-data-collector-dev` |

---

## API REST — Referencia de endpoints

Swagger UI interactivo disponible en `/docs`. ReDoc en `/redoc`.

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del servicio y conexión DynamoDB |
| `GET` | `/api/v1/launches` | Listar todos los lanzamientos (soporta `?status=` y `?limit=`) |
| `GET` | `/api/v1/launches/{launch_id}` | Detalle de un lanzamiento |
| `GET` | `/api/v1/launches/stats` | Totales y tasa de éxito |
| `POST` | `/api/v1/trigger` | Invocar la Lambda manualmente (dispara sincronización) |

**Filtros disponibles en `GET /api/v1/launches`:**

- `?status=success` | `failed` | `upcoming` | `unknown`
- `?limit=N` (1–500)

Los resultados siempre se retornan ordenados por `launch_date` descendente.

**Ejemplo — disparar sincronización manual:**

```bash
curl -X POST http://spacex-alb-dev-1388470716.us-east-1.elb.amazonaws.com/api/v1/trigger
# {
#   "total_fetched": 205,
#   "inserted": 3,
#   "updated": 202,
#   "errors": 0,
#   "launches": [...]
# }
```

---

## URLs públicas

El ALB provee un DNS **estable** que no cambia entre redeployments.

| Servicio | URL |
|---|---|
| **WebApp** | http://spacex-alb-dev-1388470716.us-east-1.elb.amazonaws.com |
| **API REST** | http://spacex-alb-dev-1388470716.us-east-1.elb.amazonaws.com/api/v1 |
| **Swagger UI** | http://spacex-alb-dev-1388470716.us-east-1.elb.amazonaws.com/docs |
| **ReDoc** | http://spacex-alb-dev-1388470716.us-east-1.elb.amazonaws.com/redoc |
| **API Gateway (trigger Lambda)** | https://z7i0z19trh.execute-api.us-east-1.amazonaws.com/dev/trigger |

---

## Cómo extender el sistema

### Agregar un nuevo entorno (staging, prod)

```bash
cd infra
terraform workspace new staging
terraform apply -var="environment=staging"
```

### Agregar un nuevo endpoint al Backend

1. Crear el router en `backend/routers/nuevo.py`.
2. Registrarlo en `backend/main.py`: `app.include_router(nuevo.router, prefix="/api/v1")`.
3. Agregar tests en `backend/tests/`.

### Agregar un nuevo campo de SpaceX a DynamoDB

1. Modificar `lambda/dynamo_repository.py::_map_launch()` para incluir el campo.
2. Agregar el campo al modelo Pydantic en `backend/models/launch.py`.
3. Los GSIs existentes no requieren migración (PAY_PER_REQUEST + esquema flexible de DynamoDB).

### Agregar pasos al pipeline CI/CD

Editar `.github/workflows/deploy.yml`. Cada job puede agregarse en paralelo (mismo nivel de `needs`) o secuencialmente. Los jobs de deploy solo corren en push a `main` (`if: github.ref == 'refs/heads/main' && github.event_name == 'push'`).
