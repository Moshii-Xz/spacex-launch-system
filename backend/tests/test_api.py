"""Tests para los endpoints del backend FastAPI."""
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Configurar entorno de pruebas antes de importar la app
os.environ["DYNAMODB_TABLE"]       = "spacex-launches-test"
os.environ["AWS_REGION"]           = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"]    = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"]= "testing"
os.environ["LAMBDA_FUNCTION_NAME"] = "spacex-data-collector-test"

from backend.main import app  # noqa: E402

client = TestClient(app)

# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_ITEM = {
    "launch_id":    "abc123",
    "mission_name": "Test Mission",
    "rocket_name":  "Falcon 9",
    "launch_date":  "2024-01-15T10:00:00.000Z",
    "status":       "success",
    "launchpad":    "KSC LC-39A",
    "flight_number":"100",
    "details":      "Test mission details",
    "payloads":     [],
    "webcast_url":  "",
    "article_url":  "",
    "wikipedia_url":"",
    "patch_small":  "",
    "patch_large":  "",
}

# ── Health ────────────────────────────────────────────────────────────────────

@patch("backend.routers.health.DynamoService")
def test_health_ok(mock_dynamo_cls):
    mock = MagicMock()
    mock.ping.return_value = True
    mock_dynamo_cls.return_value = mock

    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["dynamodb"] == "ok"


@patch("backend.routers.health.DynamoService")
def test_health_degraded(mock_dynamo_cls):
    mock = MagicMock()
    mock.ping.side_effect = Exception("unreachable")
    mock_dynamo_cls.return_value = mock

    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "degraded"


# ── Root ──────────────────────────────────────────────────────────────────────

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "docs" in r.json()


# ── Launches ──────────────────────────────────────────────────────────────────

@patch("backend.routers.launches.DynamoService")
def test_list_launches_returns_list(mock_cls):
    mock = MagicMock()
    mock.get_all.return_value = [SAMPLE_ITEM]
    mock.to_launch.return_value = MagicMock(**SAMPLE_ITEM)
    mock_cls.return_value = mock

    r = client.get("/api/v1/launches")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@patch("backend.routers.launches.DynamoService")
def test_list_launches_filtered_by_status(mock_cls):
    mock = MagicMock()
    mock.get_by_status.return_value = [SAMPLE_ITEM]
    mock.to_launch.return_value = MagicMock(**SAMPLE_ITEM)
    mock_cls.return_value = mock

    r = client.get("/api/v1/launches?status=success")
    assert r.status_code == 200
    mock.get_by_status.assert_called_once_with("success")


@patch("backend.routers.launches.DynamoService")
def test_get_launch_by_id_found(mock_cls):
    mock = MagicMock()
    mock.get_by_id.return_value = SAMPLE_ITEM
    mock.to_launch.return_value = MagicMock(**SAMPLE_ITEM)
    mock_cls.return_value = mock

    r = client.get("/api/v1/launches/abc123")
    assert r.status_code == 200


@patch("backend.routers.launches.DynamoService")
def test_get_launch_by_id_not_found(mock_cls):
    mock = MagicMock()
    mock.get_by_id.return_value = None
    mock_cls.return_value = mock

    r = client.get("/api/v1/launches/nonexistent")
    assert r.status_code == 404


@patch("backend.routers.launches.DynamoService")
def test_get_stats(mock_cls):
    from backend.models.launch import LaunchStats
    mock = MagicMock()
    mock.get_stats.return_value = LaunchStats(
        total=10, success=8, failed=1, upcoming=1, success_rate=88.9
    )
    mock_cls.return_value = mock

    r = client.get("/api/v1/launches/stats")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body
    assert "success_rate" in body


# ── Swagger ───────────────────────────────────────────────────────────────────

def test_openapi_schema_accessible():
    r = client.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    assert schema["info"]["title"] == "SpaceX Launch Tracker API"


def test_swagger_ui_accessible():
    r = client.get("/docs")
    assert r.status_code == 200


def test_redoc_accessible():
    r = client.get("/redoc")
    assert r.status_code == 200
