import importlib
import sys
from datetime import date, datetime
from unittest.mock import MagicMock, Mock, patch


def load_forecast():
    sys.modules.pop("forecast", None)
    with patch.dict(
        sys.modules,
        {"pandas": Mock(), "prophet": Mock(Prophet=Mock())},
    ):
        return importlib.import_module("forecast")


def test_forecast_reads_finalized_costs():
    forecast = load_forecast()
    client = Mock()
    client.execute.return_value = []

    with patch.object(forecast, "Client", return_value=client):
        forecast.forecast()

    query = client.execute.call_args.args[0]
    assert "FROM costs FINAL" in query


def test_forecast_inserts_clickhouse_date_values():
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

    rows = client.execute.call_args_list[-1].args[1]
    assert rows[0][0] == date(2026, 7, 15)
