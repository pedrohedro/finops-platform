import importlib
import sys
from datetime import date, datetime
from unittest.mock import MagicMock, Mock, patch

import pytest


def load_forecast():
    sys.modules.pop("forecast", None)
    with patch.dict(
        sys.modules,
        {"pandas": Mock(), "prophet": Mock(Prophet=Mock())},
    ):
        return importlib.import_module("forecast")


def test_main_runs_exactly_one_successful_cycle():
    forecast = load_forecast()
    calls = []

    with patch.object(forecast, "forecast", lambda: calls.append("cycle")):
        assert forecast.main() == 0

    assert calls == ["cycle"]


def test_main_returns_nonzero_for_irrecoverable_failure():
    forecast = load_forecast()

    with patch.object(
        forecast,
        "forecast",
        Mock(side_effect=RuntimeError("Prophet failed")),
    ):
        assert forecast.main() == 1


def test_forecast_propagates_database_failure():
    forecast = load_forecast()
    client = Mock()
    client.execute.side_effect = OSError("ClickHouse down")

    with (
        patch.object(forecast, "Client", return_value=client),
        pytest.raises(OSError, match="ClickHouse down"),
    ):
        forecast.forecast()


def test_forecast_propagates_model_failure():
    forecast = load_forecast()
    client = Mock()
    client.execute.return_value = [(date(2026, 7, 1), 1.0)] * 14
    forecast.Prophet.return_value.fit.side_effect = RuntimeError("Prophet failed")

    with (
        patch.object(forecast, "Client", return_value=client),
        pytest.raises(RuntimeError, match="Prophet failed"),
    ):
        forecast.forecast()


def test_forecast_reads_finalized_costs():
    forecast = load_forecast()
    client = Mock()
    client.execute.return_value = []

    with patch.object(forecast, "Client", return_value=client):
        forecast.forecast()

    query = client.execute.call_args.args[0]
    assert "FROM costs FINAL" in query
    assert len(client.execute.call_args_list) == 1
    forecast.Prophet.assert_not_called()


def test_forecast_replaces_synthetic_rows_synchronously():
    forecast = load_forecast()
    client = Mock()
    client.execute.side_effect = [[(date(2026, 7, 1), 1.0)] * 14, None, None]
    frame = MagicMock()
    series = MagicMock()
    series.max.return_value = date(2026, 7, 14)
    series.__gt__.return_value = "future"
    frame.__getitem__.return_value = series
    forecast.pd.DataFrame.return_value = frame
    forecast.pd.to_datetime.return_value = datetime(2026, 7, 14)
    future_rows = Mock(empty=False)
    future_rows.iterrows.return_value = [
        (0, {"ds": datetime(2026, 7, 15), "yhat": 12.34})
    ]
    prediction = MagicMock()
    prediction.__getitem__.side_effect = (
        lambda key: series if key == "ds" else future_rows
    )
    model = forecast.Prophet.return_value
    model.predict.return_value = prediction

    with patch.object(forecast, "Client", return_value=client):
        forecast.forecast()

    delete_call = client.execute.call_args_list[1]
    delete_query, delete_params = delete_call.args
    assert "record_type = 'forecast'" in delete_query
    assert "aws_account_id = %(account)s" in delete_query
    assert delete_params == {"account": "000000000000"}
    assert delete_call.kwargs == {"settings": {"mutations_sync": 1}}

    insert_query, rows = client.execute.call_args_list[2].args
    assert "aws_account_id" in insert_query
    assert rows == [
        (
            "000000000000",
            date(2026, 7, 15),
            "Forecasted Spend",
            12.34,
            "forecast",
        )
    ]
