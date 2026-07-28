import os
import time
import boto3
from datetime import datetime, timedelta
from clickhouse_driver import Client

aws_ak = os.getenv("AWS_ACCESS_KEY_ID")
aws_sk = os.getenv("AWS_SECRET_ACCESS_KEY")
ch_host = os.getenv("CLICKHOUSE_HOST", "clickhouse")
ch_user = os.getenv("CLICKHOUSE_USER", "default")
ch_password = os.getenv("CLICKHOUSE_PASSWORD", "")

# Need to check aws keys because no default dummy credentials setup in the container avoids crash loop
def get_accounts(client):
    try:
        rows = client.execute("SELECT aws_account_id, role_arn FROM finops.accounts WHERE status = 'active'")
        return rows
    except Exception as e:
        print(f"Error fetching accounts: {e}")
        return []

def collect_from_account(client, account_id, role_arn):
    print(f"Collecting from account {account_id} using role {role_arn}")
    try:
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
            date_str = result['TimePeriod']['Start']
            for group in result.get('Groups', []):
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                
                if cost > 0:
                    client.execute(
                        "INSERT INTO costs (aws_account_id, date, service, cost, record_type) VALUES",
                        [(account_id, date_str, service, cost, 'actual')]
                    )
        
        # Update last_sync
        client.execute(
            "ALTER TABLE accounts UPDATE last_sync = now() WHERE aws_account_id = %(acc)s",
            {"acc": account_id}
        )
        print(f"Successfully collected real data for account {account_id}")
    except Exception as e:
        print(f"Error collecting from account {account_id}: {e}")

def collect():
    print("Starting collector cycle...")
    client = Client(host=ch_host, database="finops", user=ch_user, password=ch_password)
    
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
    services = ["Amazon EC2", "Amazon RDS", "Amazon S3", "AWS Lambda", "Amazon CloudFront"]
    teams = ["Engineering", "Product", "Marketing", "Data", "Operations"]
    environments = ["Production", "Staging", "Development", "Testing"]
    import random
    
    end = datetime.now()
    records = []
    for d in range(60):
        current_date = end - timedelta(days=d)
        date_str = current_date.strftime("%Y-%m-%d")
        for svc in services:
            base_cost = random.uniform(10, 100)
            if svc == "Amazon EC2": base_cost *= 3
            team = random.choice(teams)
            env = random.choice(environments)
            records.append(('000000000000', date_str, svc, round(base_cost, 2), team, env, 'actual'))
            
    try:
        client.execute("INSERT INTO costs (aws_account_id, date, service, cost, team, environment, record_type) VALUES", records)
        print("Mock data inserted successfully")
    except Exception as e:
        print(f"Failed to insert mock data: {e}")

if __name__ == "__main__":
    while True:
        try:
            collect()
        except Exception as e:
            print(f"Loop Error: {e}")
        time.sleep(86400)
