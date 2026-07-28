import logging
import os

from clickhouse_driver import Client

logger = logging.getLogger(__name__)

ch_host = os.getenv("CLICKHOUSE_HOST", "clickhouse")
ch_port = int(os.getenv("CLICKHOUSE_PORT", "9000"))
ch_db = os.getenv("CLICKHOUSE_DB", "finops")
ch_user = os.getenv("CLICKHOUSE_USER", "default")
ch_password = os.getenv("CLICKHOUSE_PASSWORD", "")

def normalize():
    print("Normalizing records...")
    client = Client(host=ch_host, port=ch_port, database=ch_db, user=ch_user, password=ch_password)

    # Simple rule-based tagging
    client.execute(
        """
        ALTER TABLE costs UPDATE
        team = if(service LIKE '%EC2%' OR service LIKE '%RDS%', 'Platform', 'Engineering'),
        environment = if(service LIKE '%S3%', 'Production', 'Staging')
        WHERE team = '' OR environment = ''
        """,
        settings={"mutations_sync": 1},
    )
    print("Updated missing normalizer tags.")


def main():
    try:
        normalize()
    except Exception:
        logger.exception("Normalizer cycle failed")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
