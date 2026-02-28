import logging
import os
import sys

from fastapi import APIRouter

from backend.models.launch import HealthResponse
from backend.services.dynamo_service import DynamoService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Verifica el estado del servicio y la conectividad con DynamoDB.",
)
def health_check() -> HealthResponse:
    dynamo_ok = False
    try:
        dynamo_ok = DynamoService().ping()
    except Exception as exc:
        logger.warning("DynamoDB health check failed: %s", exc)

    return HealthResponse(
        status   = "ok" if dynamo_ok else "degraded",
        dynamodb = "ok" if dynamo_ok else "error",
        version  = os.environ.get("APP_VERSION", "1.0.0"),
    )
