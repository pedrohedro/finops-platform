import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

@patch("main.get_db")
def test_health_no_db(mock_get_db):
    mock_get_db.return_value = None
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["mode"] == "demo/mock"

@patch("main.get_db")
def test_summary_no_db(mock_get_db):
    mock_get_db.return_value = None
    response = client.get("/api/summary?days=30")
    assert response.status_code == 200
    data = response.json()
    assert data["total_cost"] == 14580.42
    assert data["previous_cost"] == 13200.15

@patch("main.get_db")
def test_summary_success(mock_get_db):
    # Mock db to return total 100 on first execute and 50 on second
    mock_client = MagicMock()
    mock_client.execute.side_effect = [[[100.5]], [[50.0]]]
    mock_get_db.return_value = mock_client
    
    response = client.get("/api/summary?days=30")
    assert response.status_code == 200
    data = response.json()
    assert data["total_cost"] == 100.5
    assert data["previous_cost"] == 50.0

def test_security_headers():
    response = client.get("/api/summary")
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "default-src 'self'" in response.headers.get("Content-Security-Policy", "")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
