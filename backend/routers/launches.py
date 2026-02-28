import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.models.launch import Launch, LaunchStats, LaunchStatus
from backend.services.dynamo_service import DynamoService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/launches", tags=["Launches"])


def get_dynamo() -> DynamoService:
    return DynamoService()


DynamoDep = Annotated[DynamoService, Depends(get_dynamo)]


@router.get(
    "",
    response_model=list[Launch],
    summary="Listar todos los lanzamientos",
    description="Retorna todos los lanzamientos almacenados en DynamoDB. "
                "Soporta filtrado opcional por estado.",
)
def list_launches(
    dynamo: DynamoDep,
    status: Optional[LaunchStatus] = Query(None, description="Filtrar por estado del lanzamiento"),
    limit:  Optional[int]          = Query(None, ge=1, le=500, description="Límite de resultados"),
) -> list[Launch]:
    try:
        if status:
            items = dynamo.get_by_status(status.value)
        else:
            items = dynamo.get_all(limit=limit)

        launches = [dynamo.to_launch(i) for i in items]
        launches.sort(key=lambda l: l.launch_date, reverse=True)
        return launches
    except Exception as exc:
        logger.error("Error listando lanzamientos: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener lanzamientos desde DynamoDB",
        ) from exc


@router.get(
    "/stats",
    response_model=LaunchStats,
    summary="Estadísticas generales",
    description="Retorna conteos y tasa de éxito de todos los lanzamientos.",
)
def get_stats(dynamo: DynamoDep) -> LaunchStats:
    try:
        return dynamo.get_stats()
    except Exception as exc:
        logger.error("Error calculando estadísticas: %s", exc)
        raise HTTPException(status_code=500, detail="Error al calcular estadísticas") from exc


@router.get(
    "/{launch_id}",
    response_model=Launch,
    summary="Obtener lanzamiento por ID",
    description="Retorna el detalle completo de un lanzamiento específico.",
    responses={404: {"description": "Lanzamiento no encontrado"}},
)
def get_launch(launch_id: str, dynamo: DynamoDep) -> Launch:
    try:
        item = dynamo.get_by_id(launch_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lanzamiento '{launch_id}' no encontrado",
            )
        return dynamo.to_launch(item)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error obteniendo lanzamiento %s: %s", launch_id, exc)
        raise HTTPException(status_code=500, detail="Error al obtener lanzamiento") from exc
