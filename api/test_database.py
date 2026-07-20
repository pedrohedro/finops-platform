from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

import main


@patch("main.Client")
def test_get_db_uses_clickhouse_environment(mock_client, monkeypatch):
    monkeypatch.setenv("CLICKHOUSE_HOST", "db.internal")
    monkeypatch.setenv("CLICKHOUSE_PORT", "9000")
    monkeypatch.setenv("CLICKHOUSE_DB", "finops_test")
    monkeypatch.setenv("CLICKHOUSE_USER", "reader")
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "secret")

    main.get_db()

    mock_client.assert_called_once_with(
        host="db.internal",
        port=9000,
        database="finops_test",
        user="reader",
        password="secret",
    )


@patch("main.get_db")
def test_execute_query_returns_driver_rows(mock_get_db):
    client = MagicMock()
    client.execute.return_value = [(1,)]
    mock_get_db.return_value = client

    rows = main.execute_query("SELECT %(value)s", {"value": 1})

    assert rows == [(1,)]
    client.execute.assert_called_once_with("SELECT %(value)s", {"value": 1})


@patch("main.get_db")
def test_execute_query_translates_driver_failure_to_503(mock_get_db):
    client = MagicMock()
    client.execute.side_effect = OSError("connection refused")
    mock_get_db.return_value = client

    with pytest.raises(HTTPException) as error:
        main.execute_query("SELECT 1")

    assert error.value.status_code == 503
    assert error.value.detail == "ClickHouse unavailable"
