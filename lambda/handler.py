import json
import logging
import os

from spacex_client import SpaceXClient
from dynamo_repository import DynamoRepository

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def lambda_handler(event: dict, context) -> dict:
    """
    Punto de entrada de la Lambda.
    Soporta invocación automática (EventBridge) e invocación manual (API Gateway).
    """
    logger.info("Iniciando recolección de datos de SpaceX")
    logger.info("Evento recibido: %s", json.dumps(event))

    client = SpaceXClient()
    repo = DynamoRepository(table_name=os.environ["DYNAMODB_TABLE"])

    try:
        # Obtener lanzamientos pasados y próximos
        past_launches = client.get_past_launches()
        upcoming_launches = client.get_upcoming_launches()
        all_launches = past_launches + upcoming_launches

        logger.info("Lanzamientos obtenidos: %d", len(all_launches))

        # Upsert en DynamoDB
        result = repo.upsert_launches(all_launches)

        summary = {
            "total_fetched": len(all_launches),
            "inserted": result["inserted"],
            "updated": result["updated"],
            "errors": result["errors"],
            "launches": [
                {
                    "launch_id": l.get("id"),
                    "mission_name": l.get("name"),
                    "launch_date": l.get("date_utc"),
                    "status": _resolve_status(l),
                }
                for l in all_launches[:10]  # preview primeros 10
            ],
        }

        logger.info("Resumen: %s", json.dumps(summary))

        # Si viene de API Gateway, devolver respuesta HTTP
        if "requestContext" in event or "httpMethod" in event:
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(summary),
            }

        return summary

    except Exception as exc:
        logger.error("Error en la ejecución: %s", str(exc), exc_info=True)
        if "requestContext" in event or "httpMethod" in event:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": str(exc)}),
            }
        raise


def _resolve_status(launch: dict) -> str:
    """Determina el estado del lanzamiento basado en los datos de la API."""
    if launch.get("upcoming"):
        return "upcoming"
    success = launch.get("success")
    if success is True:
        return "success"
    if success is False:
        return "failed"
    return "unknown"
