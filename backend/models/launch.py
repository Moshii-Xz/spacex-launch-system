from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class LaunchStatus(str, Enum):
    success  = "success"
    failed   = "failed"
    upcoming = "upcoming"
    unknown  = "unknown"


class Launch(BaseModel):
    launch_id:     str            = Field(..., description="ID único del lanzamiento")
    mission_name:  str            = Field(..., description="Nombre de la misión")
    rocket_name:   str            = Field("",  description="Nombre del cohete")
    launch_date:   str            = Field(..., description="Fecha UTC del lanzamiento (ISO 8601)")
    status:        LaunchStatus   = Field(..., description="Estado del lanzamiento")
    launchpad:     Optional[str]  = Field("",  description="Plataforma de lanzamiento")
    flight_number: Optional[str]  = Field("",  description="Número de vuelo")
    details:       Optional[str]  = Field("",  description="Descripción del lanzamiento")
    payloads:      list[str]      = Field(default_factory=list, description="IDs de cargas útiles")
    webcast_url:   Optional[str]  = Field("",  description="URL del webcast")
    article_url:   Optional[str]  = Field("",  description="URL del artículo")
    wikipedia_url: Optional[str]  = Field("",  description="URL de Wikipedia")
    patch_small:   Optional[str]  = Field("",  description="URL del parche pequeño")
    patch_large:   Optional[str]  = Field("",  description="URL del parche grande")

    model_config = {
        "json_schema_extra": {
            "example": {
                "launch_id":    "5eb87cd9ffd86e000604b32a",
                "mission_name": "FalconSat",
                "rocket_name":  "Falcon 1",
                "launch_date":  "2006-03-24T22:30:00.000Z",
                "status":       "failed",
                "launchpad":    "Omelek Island",
                "flight_number": "1",
                "details":      "Engine failure at T+33 seconds",
                "payloads":     ["5eb0e4b5b6c3bb0006eeb1e1"],
                "webcast_url":  "https://www.youtube.com/watch?v=0a_00nJ_Y88",
                "patch_small":  "https://images2.imgbox.com/94/f2/NN6Ph45r_o.png",
            }
        }
    }


class LaunchStats(BaseModel):
    total:        int   = Field(..., description="Total de lanzamientos en la base de datos")
    success:      int   = Field(..., description="Lanzamientos exitosos")
    failed:       int   = Field(..., description="Lanzamientos fallidos")
    upcoming:     int   = Field(..., description="Lanzamientos próximos")
    success_rate: float = Field(..., description="Tasa de éxito en porcentaje (0-100)")


class SyncResponse(BaseModel):
    total_fetched: int        = Field(..., description="Total de registros obtenidos de la API SpaceX")
    inserted:      int        = Field(..., description="Registros nuevos insertados")
    updated:       int        = Field(..., description="Registros existentes actualizados")
    errors:        int        = Field(..., description="Errores durante el proceso")
    launches:      list[dict] = Field(default_factory=list, description="Preview de los primeros 10 lanzamientos procesados")


class HealthResponse(BaseModel):
    status:   str = Field(..., description="Estado del servicio: ok | degraded")
    dynamodb: str = Field(..., description="Estado de la conexión a DynamoDB: ok | error")
    version:  str = Field("1.0.0", description="Versión de la API")
