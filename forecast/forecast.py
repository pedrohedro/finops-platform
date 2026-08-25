import os
import pandas as pd
from clickhouse_driver import Client
from prophet import Prophet
import logging

# Suppress Prophet logs
logging.getLogger('prophet').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

ch_host = os.getenv("CLICKHOUSE_HOST", "clickhouse")
ch_port = int(os.getenv("CLICKHOUSE_PORT", "9000"))
ch_db = os.getenv("CLICKHOUSE_DB", "finops")
ch_user = os.getenv("CLICKHOUSE_USER", "default")
ch_password = os.getenv("CLICKHOUSE_PASSWORD", "")

def forecast():
    print("Running forecast...")
    client = Client(host=ch_host, port=ch_port, database=ch_db, user=ch_user, password=ch_password)

    # Get historical data
    rows = client.execute("""
        SELECT date, sum(cost)
        FROM costs FINAL
        WHERE record_type = 'actual'
        GROUP BY date
        ORDER BY date
    """)

    if len(rows) < 14:
        print(f"Not enough data to forecast. Found {len(rows)} days. Need at least 14.")
        return

    df = pd.DataFrame(rows, columns=['ds', 'y'])

    # Train model
    m = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False)
    m.fit(df)

    # Predict 30 days
    future = m.make_future_dataframe(periods=30)
    fcst = m.predict(future)

    # Filter only future dates
    last_actual_date = df['ds'].max()
    future_fcst = fcst[fcst['ds'] > pd.to_datetime(last_actual_date)]

    if future_fcst.empty:
        return

    # Clean old forecasts from the platform-wide synthetic scope.
    client.execute(
        """
        ALTER TABLE costs DELETE
        WHERE record_type = 'forecast' AND aws_account_id = %(account)s
        """,
        {"account": "000000000000"},
        settings={"mutations_sync": 1},
    )

    records = []
    for _, row in future_fcst.iterrows():
        date_value = row['ds'].date()
        records.append(
            (
                "000000000000",
                date_value,
                "Forecasted Spend",
                round(row['yhat'], 2),
                "forecast",
            )
        )

    if records:
        client.execute(
            "INSERT INTO costs (aws_account_id, date, service, cost, record_type) VALUES",
            records,
        )
        print(f"Inserted {len(records)} forecast records.")


def main():
    try:
        forecast()
    except Exception:
        logger.exception("Forecast cycle failed")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
