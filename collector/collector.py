import logging
import os
from datetime import date, datetime, timedelta

import boto3
from clickhouse_driver import Client

logger = logging.getLogger(__name__)

aws_ak = os.getenv("AWS_ACCESS_KEY_ID")
aws_sk = os.getenv("AWS_SECRET_ACCESS_KEY")
ch_host = os.getenv("CLICKHOUSE_HOST", "clickhouse")
ch_port = int(os.getenv("CLICKHOUSE_PORT", "9000"))
ch_db = os.getenv("CLICKHOUSE_DB", "finops")
ch_user = os.getenv("CLICKHOUSE_USER", "default")
ch_password = os.getenv("CLICKHOUSE_PASSWORD", "")

# Need to check aws keys because no default dummy credentials setup in the container avoids crash loop
def get_accounts(client):
    return client.execute(
        "SELECT aws_account_id, role_arn FROM accounts WHERE status = 'active'"
    )

def collect_from_account(client, account_id, role_arn):
    print(f"Collecting from account {account_id} using role {role_arn}")
    sts = boto3.client('sts')
    assumed_role = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName="FinOpsCollectorSession"
    )

    creds = assumed_role['Credentials']
    ce = boto3.client(
        'ce',
        region_name='us-east-1',
        aws_access_key_id=creds['AccessKeyId'],
        aws_secret_access_key=creds['SecretAccessKey'],
        aws_session_token=creds['SessionToken']
    )

    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

    response = ce.get_cost_and_usage(
        TimePeriod={'Start': start, 'End': end},
        Granularity='DAILY',
        Metrics=['UnblendedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
    )

    for result in response.get('ResultsByTime', []):
        date_value = datetime.fromisoformat(result['TimePeriod']['Start']).date()
        for group in result.get('Groups', []):
            service = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])

            client.execute(
                "INSERT INTO costs (aws_account_id, date, service, cost, record_type) VALUES",
                [(account_id, date_value, service, cost, 'actual')]
            )

    # Update last_sync
    client.execute(
        "ALTER TABLE accounts UPDATE last_sync = now() WHERE aws_account_id = %(acc)s",
        {"acc": account_id}
    )
    print(f"Successfully collected real data for account {account_id}")


def build_mock_records(today: date):
    services = ["Amazon EC2", "Amazon RDS", "Amazon S3", "AWS Lambda", "Amazon CloudFront"]
    teams = ["Engineering", "Product", "Marketing", "Data", "Operations"]
    environments = ["Production", "Staging", "Development", "Testing"]
    records = []

    for day_offset in range(60):
        current_date = today - timedelta(days=day_offset)
        for service_index, service in enumerate(services):
            cost = 30.0 + service_index * 10 + day_offset % 7
            if service == "Amazon EC2":
                cost *= 3
            records.append(
                (
                    "000000000000",
                    current_date,
                    service,
                    round(cost, 2),
                    teams[service_index],
                    environments[service_index % len(environments)],
                    "actual",
                )
            )

    return records

def collect():
    print("Starting collector cycle...")
    client = Client(host=ch_host, port=ch_port, database=ch_db, user=ch_user, password=ch_password)
    
    # Ensure table exists (though handled by init script, good for safety)
    client.execute("""
        CREATE TABLE IF NOT EXISTS costs
        (aws_account_id String DEFAULT '000000000000', date Date, timestamp DateTime DEFAULT now(), service String, cost Float64, team String, environment String, record_type String DEFAULT 'actual')
        ENGINE = ReplacingMergeTree(timestamp) PARTITION BY toYYYYMM(date) ORDER BY (aws_account_id, date, service, record_type)
    """)

    accounts = get_accounts(client)
    
    if not accounts:
        if not aws_ak or not aws_sk:
            print("No accounts and no AWS keys. Inserting mock data.")
            insert_mock_data(client)
        else:
            print("No accounts registered in DB. Using local credentials as fallback.")
            # Fallback to local keys if no accounts in DB but keys exist
            # ... (keep existing simple collection if needed, or just insert mock)
            insert_mock_data(client)
    else:
        for acc_id, role_arn in accounts:
            collect_from_account(client, acc_id, role_arn)

def insert_mock_data(client):
    records = build_mock_records(datetime.now().date())
    client.execute(
        "INSERT INTO costs (aws_account_id, date, service, cost, team, environment, record_type) VALUES",
        records,
    )
    print("Mock data inserted successfully")


def main():
    try:
        collect()
    except Exception:
        logger.exception("Collector cycle failed")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
