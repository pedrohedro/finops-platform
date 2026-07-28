from unittest.mock import Mock

import collector


def test_collect_from_account_preserves_aws_account_id(monkeypatch):
    sts = Mock()
    sts.assume_role.return_value = {
        "Credentials": {
            "AccessKeyId": "key",
            "SecretAccessKey": "secret",
            "SessionToken": "token",
        }
    }

    cost_explorer = Mock()
    cost_explorer.get_cost_and_usage.return_value = {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2026-07-27"},
                "Groups": [
                    {
                        "Keys": ["Amazon EC2"],
                        "Metrics": {
                            "UnblendedCost": {"Amount": "12.34"}
                        },
                    }
                ],
            }
        ]
    }

    def boto3_client(service, **kwargs):
        return {"sts": sts, "ce": cost_explorer}[service]

    monkeypatch.setattr(collector.boto3, "client", boto3_client)

    clickhouse = Mock()
    collector.collect_from_account(
        clickhouse,
        "123456789012",
        "arn:aws:iam::123456789012:role/FinOpsCollector",
    )

    insert_call = next(
        call
        for call in clickhouse.execute.call_args_list
        if "INSERT INTO costs" in call.args[0]
    )
    sql, rows = insert_call.args

    assert "aws_account_id" in sql
    assert "123456789012" in rows[0]


def test_insert_mock_data_uses_synthetic_account_id():
    clickhouse = Mock()

    collector.insert_mock_data(clickhouse)

    sql, rows = clickhouse.execute.call_args.args
    assert "aws_account_id" in sql
    assert {row[0] for row in rows} == {"000000000000"}
