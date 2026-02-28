"""Tests unitarios para el handler principal de la Lambda."""
import json
import os
from unittest.mock import MagicMock, patch

import pytest

os.environ["DYNAMODB_TABLE"] = "spacex-launches-test"
os.environ["LOG_LEVEL"] = "ERROR"

from handler import lambda_handler, _resolve_status


# ─── Tests de _resolve_status ────────────────────────────────────────────────

def test_resolve_status_upcoming():
    assert _resolve_status({"upcoming": True}) == "upcoming"


def test_resolve_status_success():
    assert _resolve_status({"upcoming": False, "success": True}) == "success"


def test_resolve_status_failed():
    assert _resolve_status({"upcoming": False, "success": False}) == "failed"


def test_resolve_status_unknown():
    assert _resolve_status({"upcoming": False, "success": None}) == "unknown"


# ─── Tests del handler completo ──────────────────────────────────────────────

@patch("handler.DynamoRepository")
@patch("handler.SpaceXClient")
def test_handler_returns_summary(mock_client_cls, mock_repo_cls, sample_launches):
    """El handler debe retornar un resumen con conteos correctos."""
    mock_client = MagicMock()
    mock_client.get_past_launches.return_value = [sample_launches[0]]
    mock_client.get_upcoming_launches.return_value = [sample_launches[1]]
    mock_client_cls.return_value = mock_client

    mock_repo = MagicMock()
    mock_repo.upsert_launches.return_value = {"inserted": 2, "updated": 0, "errors": 0}
    mock_repo_cls.return_value = mock_repo

    result = lambda_handler({}, None)

    assert result["total_fetched"] == 2
    assert result["inserted"] == 2
    assert result["errors"] == 0


@patch("handler.DynamoRepository")
@patch("handler.SpaceXClient")
def test_handler_returns_http_response_for_api_gateway(mock_client_cls, mock_repo_cls,
                                                        sample_launches):
    """Si viene de API Gateway debe retornar statusCode 200."""
    mock_client = MagicMock()
    mock_client.get_past_launches.return_value = []
    mock_client.get_upcoming_launches.return_value = []
    mock_client_cls.return_value = mock_client

    mock_repo = MagicMock()
    mock_repo.upsert_launches.return_value = {"inserted": 0, "updated": 0, "errors": 0}
    mock_repo_cls.return_value = mock_repo

    event = {"requestContext": {"http": {"method": "POST"}}}
    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert "total_fetched" in body


@patch("handler.DynamoRepository")
@patch("handler.SpaceXClient")
def test_handler_returns_500_on_error(mock_client_cls, mock_repo_cls):
    """Si ocurre un error debe retornar statusCode 500 cuando viene de API Gateway."""
    mock_client = MagicMock()
    mock_client.get_past_launches.side_effect = Exception("API down")
    mock_client_cls.return_value = mock_client

    event = {"requestContext": {}}
    result = lambda_handler(event, None)

    assert result["statusCode"] == 500
    body = json.loads(result["body"])
    assert "error" in body
