from unittest.mock import patch
from uuid import UUID

from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


@patch("main.execute_query", return_value=[(100.5, 50.0)])
def test_summary_uses_clickhouse(mock_execute):
    response = client.get("/api/summary?days=30")
    assert response.status_code == 200
    assert response.json() == {"total_cost": 100.5, "previous_cost": 50.0}
    assert "sumIf" in mock_execute.call_args.args[0]


@patch("main.execute_query", return_value=[("EC2", 80.0), ("S3", 20.0)])
def test_services_preserves_response_shape(mock_execute):
    response = client.get("/api/services?days=30&limit=2")
    assert response.status_code == 200
    assert response.json() == [
        {"name": "EC2", "cost": 80.0},
        {"name": "S3", "cost": 20.0},
    ]


@patch("main.execute_query", return_value=[("2026-07-20", 10.5, "actual")])
def test_daily_preserves_response_shape(mock_execute):
    response = client.get("/api/daily?days=7")
    assert response.status_code == 200
    assert response.json() == [
        {"date": "2026-07-20", "cost": 10.5, "type": "actual"}
    ]


@patch("main.execute_query", return_value=[("Production", 25.0)])
def test_breakdown_preserves_response_shape(mock_execute):
    response = client.get("/api/breakdown?days=7")
    assert response.json() == [{"name": "Production", "cost": 25.0}]


@patch("main.execute_query", return_value=[("Platform", 25.0)])
def test_teams_preserves_response_shape(mock_execute):
    response = client.get("/api/teams?days=7")
    assert response.json() == [{"name": "Platform", "cost": 25.0}]


@patch(
    "main.execute_query",
    return_value=[("2026-07-20", "EC2", "Platform", "Production", 25.0, "actual")],
)
def test_details_preserves_response_shape(mock_execute):
    response = client.get("/api/details?days=7&limit=10")
    assert response.json() == [
        {
            "date": "2026-07-20",
            "service": "EC2",
            "team": "Platform",
            "environment": "Production",
            "cost": 25.0,
            "type": "actual",
        }
    ]


@patch(
    "main.execute_query",
    return_value=[
        (
            "b2be50fa-1b63-4a42-8a0f-bc959a5e36aa",
            "Production",
            "123456789012",
            "arn:aws:iam::123456789012:role/FinOpsReadOnly",
            "active",
            "2026-07-20 12:00:00",
        )
    ],
)
def test_accounts_use_clickhouse_schema(mock_execute):
    response = client.get("/api/accounts")
    assert response.status_code == 200
    assert response.json()[0]["aws_account_id"] == "123456789012"
    assert response.json()[0]["last_sync"] == "2026-07-20 12:00:00"


@patch("main.execute_query", return_value=[])
def test_create_account_returns_generated_uuid(mock_execute):
    response = client.post(
        "/api/accounts",
        json={
            "name": "Production",
            "aws_account_id": "123456789012",
            "role_arn": "arn:aws:iam::123456789012:role/FinOpsReadOnly",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "created"
    UUID(response.json()["id"])
    assert "INSERT INTO accounts" in mock_execute.call_args.args[0]


def test_query_bounds_are_validated():
    assert client.get("/api/summary?days=0").status_code == 422
    assert client.get("/api/services?limit=0").status_code == 422
    assert client.get("/api/details?limit=1001").status_code == 422


@patch(
    "main.execute_query",
    side_effect=HTTPException(status_code=503, detail="ClickHouse unavailable"),
)
def test_database_failure_returns_503(mock_execute):
    response = client.get("/api/summary")
    assert response.status_code == 503
    assert response.json() == {"detail": "ClickHouse unavailable"}


@patch("main.get_db")
def test_liveness_does_not_touch_database(mock_get_db):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    mock_get_db.assert_not_called()


@patch("main.get_db")
def test_readiness_returns_200_when_clickhouse_responds(mock_get_db):
    mock_get_db.return_value.execute.return_value = [(1,)]
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "online"}


@patch("main.get_db")
def test_readiness_returns_503_when_clickhouse_is_offline(mock_get_db):
    mock_get_db.return_value.execute.side_effect = OSError("connection refused")
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json() == {"detail": "ClickHouse unavailable"}


def test_metrics_exposes_bounded_http_labels():
    client.get("/healthz")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "finops_api_http_requests_total" in response.text
    assert 'path="/healthz"' in response.text


def test_security_headers_are_present():
    response = client.get("/healthz")
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Content-Security-Policy"] == "default-src 'self'"


def test_cors_allows_configured_local_dashboard():
    response = client.options(
        "/api/summary",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_metrics_use_constant_label_for_unmatched_paths():
    client.get("/missing-metric-path-one")
    client.get("/missing-metric-path-two")
    response = client.get("/metrics")
    assert 'path="<unmatched>"' in response.text
    assert 'path="/missing-metric-path-one"' not in response.text
    assert 'path="/missing-metric-path-two"' not in response.text
