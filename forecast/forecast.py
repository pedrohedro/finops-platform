import os
import time
import pandas as pd
from datetime import datetime, timedelta
from clickhouse_driver import Client
from prophet import Prophet
import logging

# Suppress Prophet logs
logging.getLogger('prophet').setLevel(logging.WARNING)

ch_host = os.getenv("CLICKHOUSE_HOST", "clickhouse")
ch_user = os.getenv("CLICKHOUSE_USER", "default")
ch_password = os.getenv("CLICKHOUSE_PASSWORD", "")

def forecast():
    print("Running forecast...")
    try:
        client = Client(host=ch_host, database="finops", user=ch_user, password=ch_password)
        
        # Get historical data
        rows = client.execute("""
            SELECT date, sum(cost) 
            FROM costs 
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
            
        # Clean old forecasts
        client.execute("ALTER TABLE costs DELETE WHERE record_type = 'forecast'")
        
        # Insert new forecasts
        records = []
        for _, row in future_fcst.iterrows():
            date_str = row['ds'].strftime('%Y-%m-%d')
            # Assuming main cost is platform wide, setting environment and team to ALL
            records.append((date_str, 'Forecasted Spend', round(row['yhat'], 2), 'forecast'))
            
        if records:
            client.execute("INSERT INTO costs (date, service, cost, record_type) VALUES", records)
            print(f"Inserted {len(records)} forecast records.")
            
    except Exception as e:
        print(f"Forecast Error: {e}")

if __name__ == "__main__":
    while True:
        try:
            forecast()
        except Exception as e:
            print(e)
        time.sleep(86400)
