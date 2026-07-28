CREATE DATABASE IF NOT EXISTS finops;

CREATE TABLE IF NOT EXISTS finops.costs
(
    aws_account_id String DEFAULT '000000000000',
    date Date,
    timestamp DateTime DEFAULT now(),
    service String,
    cost Float64,
    team String,
    environment String,
    record_type String DEFAULT 'actual'
)
ENGINE = ReplacingMergeTree(timestamp)
PARTITION BY toYYYYMM(date)
ORDER BY (aws_account_id, date, service, record_type);

CREATE TABLE IF NOT EXISTS finops.accounts
(
    id UUID DEFAULT generateUUIDv4(),
    name String,
    aws_account_id String,
    role_arn String,
    status String DEFAULT 'active',
    last_sync DateTime DEFAULT now(),
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY id;
