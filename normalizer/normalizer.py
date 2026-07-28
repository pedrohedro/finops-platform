import os
import time
from clickhouse_driver import Client

ch_host = os.getenv("CLICKHOUSE_HOST", "clickhouse")
ch_port = int(os.getenv("CLICKHOUSE_PORT", "9000"))
ch_db = os.getenv("CLICKHOUSE_DB", "finops")
ch_user = os.getenv("CLICKHOUSE_USER", "default")
ch_password = os.getenv("CLICKHOUSE_PASSWORD", "")

def normalize():
    print("Normalizing records...")
    try:
        client = Client(host=ch_host, port=ch_port, database=ch_db, user=ch_user, password=ch_password)
        
        # Simple rule-based tagging
        client.execute("""
            ALTER TABLE costs UPDATE 
            team = if(service LIKE '%EC2%' OR service LIKE '%RDS%', 'Platform', 'Engineering'),
            environment = if(service LIKE '%S3%', 'Production', 'Staging')
            WHERE team = '' OR environment = ''
        """)
        print("Updated missing normalizer tags.")
    except Exception as e:
        print(f"Normalizer Error: {e}")

if __name__ == "__main__":
    while True:
        try:
            normalize()
        except Exception as e:
            print(e)
        time.sleep(3600)
