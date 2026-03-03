import json
import logging
import os
from typing import Any
import urllib.request
import urllib.error

import boto3
from fastapi import APIRouter, HTTPException

from backend.models.launch import SyncResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Sync"])

LAMBDA_FUNCTION   = os.environ.get("LAMBDA_FUNCTION_NAME", "spacex-data-collector-dev")
AWS_REGION        = os.environ.get("AWS_REGION", "us-east-1")
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")          # presente solo en local
DYNAMODB_TABLE    = os.environ.get("DYNAMODB_TABLE", "spacex-launches-dev")
SPACEX_BASE_URL   = "https://api.spacexdata.com/v4"


def _fetch_json(url: str) -> Any:
    """Petición GET simple usando urllib (sin dependencias extra)."""
    req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _resolve_status(launch: dict) -> str:
    if launch.get("upcoming"):
        return "upcoming"
    success = launch.get("success")
    if success is True:
        return "success"
    if success is False:
        return "failed"
    return "unknown"


def _map_launch(launch: dict) -> dict:
    return {
        "launch_id":     launch.get("id", ""),
        "mission_name":  launch.get("name", ""),
        "rocket_name":   launch.get("rocket", ""),
        "launch_date":   launch.get("date_utc", ""),
        "status":        _resolve_status(launch),
        "launchpad":     launch.get("launchpad", ""),
        "flight_number": str(launch.get("flight_number", "")),
        "details":       launch.get("details") or "",
        "payloads":      launch.get("payloads", []),
        "webcast_url":   launch.get("links", {}).get("webcast") or "",
        "article_url":   launch.get("links", {}).get("article") or "",
        "wikipedia_url": launch.get("links", {}).get("wikipedia") or "",
        "patch_small":   launch.get("links", {}).get("patch", {}).get("small") or "",
        "patch_large":   launch.get("links", {}).get("patch", {}).get("large") or "",
    }


def _sync_local() -> SyncResponse:
    """Modo local: llama a SpaceX API y escribe directo en DynamoDB-local."""
    logger.info("[LOCAL MODE] Sincronizando desde SpaceX API directamente...")

    past     = _fetch_json(f"{SPACEX_BASE_URL}/launches/past")
    upcoming = _fetch_json(f"{SPACEX_BASE_URL}/launches/upcoming")
    all_launches = past + upcoming
    logger.info("[LOCAL MODE] Lanzamientos obtenidos: %d", len(all_launches))

    kwargs = {"region_name": AWS_REGION, "endpoint_url": DYNAMODB_ENDPOINT}
    dynamodb = boto3.resource("dynamodb", **kwargs)
    table    = dynamodb.Table(DYNAMODB_TABLE)

    inserted = updated = errors = 0
    for launch in all_launches:
        try:
            item = _map_launch(launch)
            existing = table.get_item(Key={"launch_id": item["launch_id"]}).get("Item")
            table.put_item(Item=item)
            if existing:
                updated += 1
            else:
                inserted += 1
        except Exception as exc:
            logger.error("Error upsert %s: %s", launch.get("id"), exc)
            errors += 1

    preview = [
        {"launch_id": l.get("id"), "mission_name": l.get("name"), "status": _resolve_status(l)}
        for l in all_launches[:10]
    ]
    return SyncResponse(
        total_fetched=len(all_launches),
        inserted=inserted,
        updated=updated,
        errors=errors,
        launches=preview,
    )


@router.post(
    "/trigger",
    response_model=SyncResponse,
    summary="Invocar sincronización manual",
    description=(
        "En AWS invoca la Lambda. En local llama a SpaceX API directamente. "
        "Retorna un resumen de registros insertados/actualizados en DynamoDB."
    ),
)
def trigger_sync() -> SyncResponse:
    # ── Modo local: DYNAMODB_ENDPOINT presente → no hay Lambda disponible ──
    if DYNAMODB_ENDPOINT:
        try:
            return _sync_local()
        except Exception as exc:
            logger.error("Error en sincronización local: %s", exc)
            raise HTTPException(status_code=500, detail=f"Error en sync local: {exc}") from exc

    # ── Modo AWS: invocar Lambda real ───────────────────────────────────────
    try:
        lambda_client = boto3.client("lambda", region_name=AWS_REGION)
        response = lambda_client.invoke(
            FunctionName   = LAMBDA_FUNCTION,
            InvocationType = "RequestResponse",
            Payload        = json.dumps({"source": "manual-trigger"}),
        )

        payload_bytes: bytes = response["Payload"].read()
        result: Any = json.loads(payload_bytes)

        if response.get("FunctionError"):
            logger.error("Lambda function error: %s", result)
            raise HTTPException(status_code=502, detail=f"Lambda error: {result}")

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
