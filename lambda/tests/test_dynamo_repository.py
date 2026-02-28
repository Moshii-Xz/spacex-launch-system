"""Tests unitarios para DynamoRepository usando moto (mock de AWS)."""
import os

import boto3
import pytest
from moto import mock_aws

from dynamo_repository import DynamoRepository, DynamoRepositoryError

TABLE_NAME = "spacex-launches-test"
REGION = "us-east-1"


@pytest.fixture(autouse=True)
def aws_credentials():
    """Credenciales falsas para que moto no intente conectar a AWS real."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = REGION


@pytest.fixture
def dynamodb_table():
    """Crea una tabla DynamoDB falsa con moto."""
    with mock_aws():
        ddb = boto3.resource("dynamodb", region_name=REGION)
        table = ddb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "launch_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "launch_id", "AttributeType": "S"},
                {"AttributeName": "status", "AttributeType": "S"},
                {"AttributeName": "launch_date", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "status-index",
                    "KeySchema": [{"AttributeName": "status", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "launch_date-index",
                    "KeySchema": [{"AttributeName": "launch_date", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
        )
        table.wait_until_exists()
        yield table


@mock_aws
def test_upsert_inserts_new_launch(dynamodb_table, past_launch):
    """Debe insertar un lanzamiento nuevo."""
    repo = DynamoRepository(table_name=TABLE_NAME, region=REGION)
    result = repo.upsert_launches([past_launch])
    assert result["inserted"] == 1
    assert result["updated"] == 0
    assert result["errors"] == 0


@mock_aws
def test_upsert_updates_existing_launch(dynamodb_table, past_launch):
    """Debe actualizar un lanzamiento que ya existe."""
    repo = DynamoRepository(table_name=TABLE_NAME, region=REGION)
    repo.upsert_launches([past_launch])
    # Segunda inserción del mismo ID → update
    result = repo.upsert_launches([past_launch])
    assert result["updated"] == 1
    assert result["inserted"] == 0


@mock_aws
def test_upsert_maps_status_correctly(dynamodb_table, past_launch, upcoming_launch):
    """Debe mapear correctamente el estado de cada lanzamiento."""
    repo = DynamoRepository(table_name=TABLE_NAME, region=REGION)
    repo.upsert_launches([past_launch, upcoming_launch])
    items = repo.get_all_launches()
    statuses = {i["launch_id"]: i["status"] for i in items}
    assert statuses[past_launch["id"]] == "failed"
    assert statuses[upcoming_launch["id"]] == "upcoming"


@mock_aws
def test_get_all_launches_returns_all(dynamodb_table, sample_launches):
    """Debe retornar todos los lanzamientos almacenados."""
    repo = DynamoRepository(table_name=TABLE_NAME, region=REGION)
    repo.upsert_launches(sample_launches)
    items = repo.get_all_launches()
    assert len(items) == 2


@mock_aws
def test_get_by_status_filters_correctly(dynamodb_table, sample_launches):
    """Debe filtrar lanzamientos por estado."""
    repo = DynamoRepository(table_name=TABLE_NAME, region=REGION)
    repo.upsert_launches(sample_launches)
    upcoming = repo.get_by_status("upcoming")
    assert all(i["status"] == "upcoming" for i in upcoming)
