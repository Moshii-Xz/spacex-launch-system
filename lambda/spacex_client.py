import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

SPACEX_BASE_URL = "https://api.spacexdata.com/v4"
DEFAULT_TIMEOUT = 30


class SpaceXAPIError(Exception):
    """Error al consumir la API de SpaceX."""


class SpaceXClient:
    """Cliente HTTP para la API pública de SpaceX v4."""

    def __init__(self, base_url: str = SPACEX_BASE_URL, timeout: int = DEFAULT_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def get_past_launches(self) -> list[dict[str, Any]]:
        """Obtiene todos los lanzamientos pasados."""
        logger.info("Obteniendo lanzamientos pasados...")
        return self._get("/launches/past")

    def get_upcoming_launches(self) -> list[dict[str, Any]]:
        """Obtiene los lanzamientos próximos."""
        logger.info("Obteniendo lanzamientos próximos...")
        return self._get("/launches/upcoming")

    def get_all_launches(self) -> list[dict[str, Any]]:
        """Obtiene todos los lanzamientos (pasados + próximos)."""
        logger.info("Obteniendo todos los lanzamientos...")
        return self._get("/launches")

    def get_launch_by_id(self, launch_id: str) -> dict[str, Any]:
        """Obtiene un lanzamiento específico por ID."""
        logger.info("Obteniendo lanzamiento ID: %s", launch_id)
        return self._get(f"/launches/{launch_id}")

    def _get(self, path: str) -> Any:
        """Realiza una petición GET y maneja errores."""
        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as exc:
            raise SpaceXAPIError(f"Timeout al conectar con {url}") from exc
        except requests.exceptions.ConnectionError as exc:
            raise SpaceXAPIError(f"Error de conexión con {url}") from exc
        except requests.exceptions.HTTPError as exc:
            raise SpaceXAPIError(
                f"HTTP {exc.response.status_code} al llamar {url}: {exc.response.text}"
            ) from exc
        except requests.exceptions.JSONDecodeError as exc:
            raise SpaceXAPIError(f"Respuesta no es JSON válido desde {url}") from exc
