import logging
import os
from typing import Optional

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError

from backend.models.launch import Launch, LaunchStats

logger = logging.getLogger(__name__)


class DynamoService:
    """Capa de acceso a DynamoDB para el backend API."""

    def __init__(self) -> None:
        region = os.environ.get("AWS_REGION", "us-east-1")
        endpoint = os.environ.get("DYNAMODB_ENDPOINT")  # para DynamoDB local

        kwargs: dict = {"region_name": region}
        if endpoint:
            kwargs["endpoint_url"] = endpoint

        self.dynamodb = boto3.resource("dynamodb", **kwargs)
        self.table_name = os.environ.get("DYNAMODB_TABLE", "spacex-launches-dev")
        self.table = self.dynamodb.Table(self.table_name)

    # ── Salud ──────────────────────────────────────────────────────────────────

    def ping(self) -> bool:
        """Verifica conectividad con DynamoDB."""
        try:
            self.table.table_status  # noqa: B018
            return True
        except Exception:
            return False

    # ── Consultas ──────────────────────────────────────────────────────────────

    def get_all(self, limit: Optional[int] = None) -> list[dict]:
        """Escanea todos los registros con paginación interna."""
        try:
            kwargs: dict = {}
            if limit:
                kwargs["Limit"] = limit

            response = self.table.scan(**kwargs)
            items = response.get("Items", [])

            while "LastEvaluatedKey" in response and (limit is None or len(items) < limit):
                response = self.table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
                items.extend(response.get("Items", []))

            return items
        except (BotoCoreError, ClientError) as exc:
            logger.error("Error al escanear DynamoDB: %s", exc)
            raise

    def get_by_id(self, launch_id: str) -> Optional[dict]:
        """Obtiene un lanzamiento por su ID primario."""
        try:
            response = self.table.get_item(Key={"launch_id": launch_id})
            return response.get("Item")
        except (BotoCoreError, ClientError) as exc:
            logger.error("Error al obtener lanzamiento %s: %s", launch_id, exc)
            raise

    def get_by_status(self, status: str) -> list[dict]:
        """Filtra lanzamientos por estado usando el GSI status-index."""
        try:
            response = self.table.query(
                IndexName="status-index",
                KeyConditionExpression=Key("status").eq(status),
            )
            return response.get("Items", [])
        except (BotoCoreError, ClientError) as exc:
            logger.error("Error al filtrar por estado %s: %s", status, exc)
            raise

    # ── Estadísticas ───────────────────────────────────────────────────────────

    def get_stats(self) -> LaunchStats:
        """Calcula estadísticas de todos los lanzamientos."""
        items = self.get_all()
        total    = len(items)
        success  = sum(1 for i in items if i.get("status") == "success")
        failed   = sum(1 for i in items if i.get("status") == "failed")
        upcoming = sum(1 for i in items if i.get("status") == "upcoming")
        rate = round(success / (success + failed) * 100, 1) if (success + failed) > 0 else 0.0

        return LaunchStats(
            total=total,
            success=success,
            failed=failed,
            upcoming=upcoming,
            success_rate=rate,
        )

    # ── Utilidades ────────────────────────────────────────────────────────────

    @staticmethod
    def to_launch(item: dict) -> Launch:
        """Convierte un item de DynamoDB a modelo Pydantic."""
        return Launch(
            launch_id     = item.get("launch_id", ""),
            mission_name  = item.get("mission_name", ""),
            rocket_name   = item.get("rocket_name", ""),
            launch_date   = item.get("launch_date", ""),
            status        = item.get("status", "unknown"),
            launchpad     = item.get("launchpad", ""),
            flight_number = str(item.get("flight_number", "")),
            details       = item.get("details", ""),
            payloads      = list(item.get("payloads", [])),
            webcast_url   = item.get("webcast_url", ""),
            article_url   = item.get("article_url", ""),
            wikipedia_url = item.get("wikipedia_url", ""),
            patch_small   = item.get("patch_small", ""),
            patch_large   = item.get("patch_large", ""),
        )
