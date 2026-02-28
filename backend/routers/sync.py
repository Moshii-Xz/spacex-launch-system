import json
import logging
import os
from typing import Any

import boto3
from fastapi import APIRouter, HTTPException

from backend.models.launch import SyncResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Sync"])

LAMBDA_FUNCTION = os.environ.get("LAMBDA_FUNCTION_NAME", "spacex-data-collector-dev")
AWS_REGION      = os.environ.get("AWS_REGION", "us-east-1")


@router.post(
    "/trigger",
    response_model=SyncResponse,
    summary="Invocar sincronización manual",
    description=(
        "Invoca la función Lambda de SpaceX directamente y retorna un resumen "
        "de los registros insertados/actualizados en DynamoDB. "
        "Útil para forzar una actualización sin esperar el schedule de 6 horas."
    ),
)
def trigger_sync() -> SyncResponse:
    try:
        lambda_client = boto3.client("lambda", region_name=AWS_REGION)
        response = lambda_client.invoke(
            FunctionName   = LAMBDA_FUNCTION,
            InvocationType = "RequestResponse",
            Payload        = json.dumps({"source": "manual-trigger"}),
        )

        payload_bytes: bytes = response["Payload"].read()
        result: Any = json.loads(payload_bytes)

        # Si Lambda devolvió error funcional
        if response.get("FunctionError"):
            logger.error("Lambda function error: %s", result)
            raise HTTPException(status_code=502, detail=f"Lambda error: {result}")

        # Si Lambda devolvió respuesta HTTP (API Gateway wrapping)
        if isinstance(result, dict) and "body" in result:
            result = json.loads(result["body"])

        return SyncResponse(
            total_fetched = result.get("total_fetched", 0),
            inserted      = result.get("inserted", 0),
            updated       = result.get("updated", 0),
            errors        = result.get("errors", 0),
            launches      = result.get("launches", []),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error invocando Lambda: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Error al invocar la función Lambda: {exc}",
        ) from exc
