"""Tests unitarios para SpaceXClient."""
import pytest
import requests_mock as req_mock

from spacex_client import SpaceXClient, SpaceXAPIError


BASE_URL = "https://api.spacexdata.com/v4"


def test_get_past_launches_returns_list(requests_mock, past_launch):
    """Debe retornar una lista de lanzamientos pasados."""
    requests_mock.get(f"{BASE_URL}/launches/past", json=[past_launch])
    client = SpaceXClient()
    result = client.get_past_launches()
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["id"] == past_launch["id"]


def test_get_upcoming_launches_returns_list(requests_mock, upcoming_launch):
    """Debe retornar una lista de lanzamientos próximos."""
    requests_mock.get(f"{BASE_URL}/launches/upcoming", json=[upcoming_launch])
    client = SpaceXClient()
    result = client.get_upcoming_launches()
    assert isinstance(result, list)
    assert result[0]["upcoming"] is True


def test_raises_on_http_error(requests_mock):
    """Debe lanzar SpaceXAPIError si la API retorna un error HTTP."""
    requests_mock.get(f"{BASE_URL}/launches/past", status_code=500,
                      text="Internal Server Error")
    client = SpaceXClient()
    with pytest.raises(SpaceXAPIError):
        client.get_past_launches()


def test_raises_on_timeout(requests_mock):
    """Debe lanzar SpaceXAPIError si hay timeout."""
    import requests
    requests_mock.get(f"{BASE_URL}/launches/past",
                      exc=requests.exceptions.Timeout)
    client = SpaceXClient()
    with pytest.raises(SpaceXAPIError, match="Timeout"):
        client.get_past_launches()


def test_raises_on_connection_error(requests_mock):
    """Debe lanzar SpaceXAPIError si hay error de conexión."""
    import requests
    requests_mock.get(f"{BASE_URL}/launches/past",
                      exc=requests.exceptions.ConnectionError)
    client = SpaceXClient()
    with pytest.raises(SpaceXAPIError, match="conexión"):
        client.get_past_launches()


def test_get_launch_by_id(requests_mock, past_launch):
    """Debe obtener un lanzamiento por su ID."""
    lid = past_launch["id"]
    requests_mock.get(f"{BASE_URL}/launches/{lid}", json=past_launch)
    client = SpaceXClient()
    result = client.get_launch_by_id(lid)
    assert result["id"] == lid
