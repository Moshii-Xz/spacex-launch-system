# SpaceX Launch System

Sistema fullstack en AWS que recolecta, almacena y visualiza datos de lanzamientos espaciales de SpaceX.

## Arquitectura

```
SpaceX API → Lambda (Python) → DynamoDB → WebApp (React) → ECS Fargate
                  ↑                              ↑
            EventBridge (6h)             API Gateway (manual)
```

## Estructura del proyecto

```
spacex-launch-system/
├── infra/              # Infraestructura como código (Terraform)
├── lambda/             # Función AWS Lambda en Python
│   └── tests/          # Tests unitarios (pytest + moto)
├── webapp/             # Aplicación web React + Vite
├── .github/workflows/  # Pipeline CI/CD (GitHub Actions)
├── docker-compose.yml  # Entorno de desarrollo local
└── README.md
```

## Requisitos previos

- [AWS CLI v2](https://aws.amazon.com/cli/)
- [Terraform >= 1.5](https://terraform.io)
- [Python 3.11+](https://python.org)
- [Node.js 20+](https://nodejs.org)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

## Despliegue desde cero

### 1. Configurar AWS CLI

```bash
aws configure
# AWS Access Key ID: <tu_key>
# AWS Secret Access Key: <tu_secret>
# Default region: us-east-1
# Default output format: json
```

### 2. Desplegar infraestructura con Terraform

```bash
cd infra
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### 3. Ejecutar tests de la Lambda

```bash
cd lambda
pip install -r requirements-dev.txt
pytest tests/ -v --cov=. --cov-report=term-missing
```

### 4. Desplegar Lambda manualmente

```bash
cd lambda
pip install -r requirements.txt -t ./package
cd package && zip -r ../dist/function.zip . && cd ..
zip -g dist/function.zip *.py
aws lambda update-function-code \
  --function-name spacex-data-collector-dev \
  --zip-file fileb://dist/function.zip
```

### 5. Construir y subir imagen Docker

```bash
# Login a ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account_id>.dkr.ecr.us-east-1.amazonaws.com

# Build y push
cd webapp
docker build -t spacex-webapp .
docker tag spacex-webapp:latest <account_id>.dkr.ecr.us-east-1.amazonaws.com/spacex-webapp-dev:latest
docker push <account_id>.dkr.ecr.us-east-1.amazonaws.com/spacex-webapp-dev:latest
```

### 6. Actualizar servicio ECS

```bash
aws ecs update-service \
  --cluster spacex-cluster-dev \
  --service spacex-webapp-service-dev \
  --force-new-deployment
```

## Desarrollo local

```bash
# Copiar variables de entorno
cp .env.example .env

# Levantar DynamoDB local + WebApp
docker-compose up
```

## Pipeline CI/CD

El pipeline se activa en cada push a `main` y ejecuta:

1. **Tests Lambda** → pytest con cobertura
2. **Tests WebApp** → vitest + build de producción
3. **Build Docker** → construye y sube imagen a ECR
4. **Deploy ECS** → actualiza el servicio Fargate
5. **Deploy Lambda** → actualiza el código de la función

### Secrets requeridos en GitHub

| Secret | Descripción |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | Access key de AWS |
| `AWS_SECRET_ACCESS_KEY` | Secret key de AWS |

## API Gateway - Invocación manual

```bash
# Obtener la URL del endpoint (tras terraform apply)
terraform -chdir=infra output api_gateway_url

# Invocar la Lambda manualmente
curl -X POST <api_gateway_url>
```

## URLs

| Servicio | URL |
|----------|-----|
| WebApp desplegada | _pendiente tras deploy_ |
| Swagger / API Docs | _pendiente tras deploy_ |
