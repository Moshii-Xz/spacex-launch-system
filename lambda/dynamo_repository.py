import logging
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


class DynamoRepositoryError(Exception):
    """Error al interactuar con DynamoDB."""


class DynamoRepository:
    """Repositorio para gestionar lanzamientos de SpaceX en DynamoDB."""

    def __init__(self, table_name: str, region: str = "us-east-1"):
        self.table_name = table_name
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)

    def upsert_launches(self, launches: list[dict[str, Any]]) -> dict[str, int]:
        """
        Inserta o actualiza (upsert) una lista de lanzamientos en DynamoDB.
        Retorna un resumen con conteos de inserted, updated y errors.
        """
        inserted = 0
        updated = 0
        errors = 0

        for launch in launches:
            try:
                item = self._map_launch(launch)
                launch_id = item["launch_id"]

                # Comprobamos si ya existe
                existing = self._get_by_id(launch_id)
                if existing:
                    self._update(item)
                    updated += 1
                    logger.debug("Actualizado: %s", launch_id)
                else:
                    self._put(item)
                    inserted += 1
                    logger.debug("Insertado: %s", launch_id)

            except (BotoCoreError, ClientError) as exc:
                logger.error("Error DynamoDB para launch %s: %s", launch.get("id"), exc)
                errors += 1
            except Exception as exc:
                logger.error("Error inesperado para launch %s: %s", launch.get("id"), exc)
                errors += 1

        logger.info("Upsert completado - Insertados: %d, Actualizados: %d, Errores: %d",
                    inserted, updated, errors)
        return {"inserted": inserted, "updated": updated, "errors": errors}

    def get_all_launches(self) -> list[dict[str, Any]]:
        """Obtiene todos los lanzamientos de la tabla."""
        try:
            response = self.table.scan()
            items = response.get("Items", [])
            # Paginación
            while "LastEvaluatedKey" in response:
                response = self.table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
                items.extend(response.get("Items", []))
            return items
        except (BotoCoreError, ClientError) as exc:
            raise DynamoRepositoryError(f"Error al escanear la tabla: {exc}") from exc

    def get_by_status(self, status: str) -> list[dict[str, Any]]:
        """Obtiene lanzamientos filtrados por estado usando el GSI."""
        try:
            response = self.table.query(
                IndexName="status-index",
                KeyConditionExpression=Key("status").eq(status),
            )
            return response.get("Items", [])
        except (BotoCoreError, ClientError) as exc:
            raise DynamoRepositoryError(f"Error al consultar por estado: {exc}") from exc

    def _get_by_id(self, launch_id: str) -> dict[str, Any] | None:
        response = self.table.get_item(Key={"launch_id": launch_id})
        return response.get("Item")

    def _put(self, item: dict[str, Any]) -> None:
        self.table.put_item(Item=item)

    def _update(self, item: dict[str, Any]) -> None:
        self.table.put_item(Item=item)  # put_item hace upsert completo

    @staticmethod
    def _map_launch(launch: dict[str, Any]) -> dict[str, Any]:
        """Transforma el payload de la API SpaceX al esquema de DynamoDB."""
        status = "upcoming"
        if not launch.get("upcoming"):
            success = launch.get("success")
            status = "success" if success is True else "failed" if success is False else "unknown"

        return {
            "launch_id":        launch.get("id", ""),
            "mission_name":     launch.get("name", ""),
            "rocket_name":      launch.get("rocket", ""),   # ID resuelto en cliente si necesario
            "launch_date":      launch.get("date_utc", ""),
            "status":           status,
            "launchpad":        launch.get("launchpad", ""),
            "flight_number":    str(launch.get("flight_number", "")),
            "details":          launch.get("details") or "",
            "payloads":         launch.get("payloads", []),
            "webcast_url":      launch.get("links", {}).get("webcast") or "",
            "article_url":      launch.get("links", {}).get("article") or "",
            "wikipedia_url":    launch.get("links", {}).get("wikipedia") or "",
            "patch_small":      launch.get("links", {}).get("patch", {}).get("small") or "",
            "patch_large":      launch.get("links", {}).get("patch", {}).get("large") or "",
        }
