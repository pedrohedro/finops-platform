from datetime import date
from unittest.mock import Mock

import collector
import pytest


def test_main_runs_exactly_one_successful_cycle(monkeypatch):
    calls = []
    monkeypatch.setattr(collector, "collect", lambda: calls.append("cycle"))

    assert collector.main() == 0
    assert calls == ["cycle"]


def test_main_returns_nonzero_for_irrecoverable_failure(monkeypatch):
    def fail():
        raise OSError("ClickHouse down")

    monkeypatch.setattr(collector, "collect", fail)

    assert collector.main() == 1


def test_get_accounts_propagates_database_failure():
    clickhouse = Mock()
    clickhouse.execute.side_effect = OSError("ClickHouse down")

    with pytest.raises(OSError, match="ClickHouse down"):
        collector.get_accounts(clickhouse)


def test_collect_from_account_propagates_aws_failure(monkeypatch):
    monkeypatch.setattr(
        collector.boto3,
        "client",
        Mock(side_effect=RuntimeError("AWS unavailable")),
    )

    with pytest.raises(RuntimeError, match="AWS unavailable"):
        collector.collect_from_account(
            Mock(),
            "123456789012",
            "arn:aws:iam::123456789012:role/FinOpsCollector",
        )


def test_mock_rows_keep_overlapping_history_stable_across_days():
    expected_first = (
        "000000000000",
        date(2026, 7, 28),
        "Amazon EC2",
        93.0,
        "Engineering",
        "Production",
        "actual",
    )

    first = {
        (row[1], row[2]): row
        for row in collector.build_mock_records(date(2026, 7, 28))
    }
    second = {
        (row[1], row[2]): row
        for row in collector.build_mock_records(date(2026, 7, 29))
    }
    overlapping_keys = first.keys() & second.keys()

    assert len(first) == 300
    assert len(overlapping_keys) == 295
    assert first[(date(2026, 7, 28), "Amazon EC2")] == expected_first
    assert all(first[key] == second[key] for key in overlapping_keys)


def test_collect_uses_mock_without_credentials_even_with_active_accounts(monkeypatch):
    executions = []

    class RecordingClient:
        def execute(self, query, rows=None):
            executions.append((query, rows))
            if "SELECT aws_account_id, role_arn" in query:
                return [
                    (
                        "123456789012",
                        "arn:aws:iam::123456789012:role/FinOpsCollector",
                    )
                ]
            return []

    def reject_aws_call(*_args, **_kwargs):
        raise AssertionError("boto3.client must not run in mock mode")

    clickhouse = RecordingClient()
    monkeypatch.setattr(collector, "Client", lambda **_kwargs: clickhouse)
    monkeypatch.setattr(collector, "aws_ak", None)
    monkeypatch.setattr(collector, "aws_sk", None)
    monkeypatch.setattr(collector.boto3, "client", reject_aws_call)

    collector.collect()

    mock_inserts = [
        rows
        for query, rows in executions
        if "INSERT INTO costs" in query
    ]
    assert len(mock_inserts) == 1
    assert {row[0] for row in mock_inserts[0]} == {"000000000000"}


def test_insert_mock_data_propagates_database_failure():
    clickhouse = Mock()
    clickhouse.execute.side_effect = OSError("insert failed")

    with pytest.raises(OSError, match="insert failed"):
        collector.insert_mock_data(clickhouse)


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
                    },
                    {
                        "Keys": ["AWS Support"],
                        "Metrics": {
                            "UnblendedCost": {"Amount": "0"}
                        },
                    },
                    {
                        "Keys": ["Credits"],
                        "Metrics": {
                            "UnblendedCost": {"Amount": "-4.20"}
                        },
                    },
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

    insert_calls = [
        call
        for call in clickhouse.execute.call_args_list
        if "INSERT INTO costs" in call.args[0]
    ]
    sql = insert_calls[0].args[0]
    rows = [call.args[1][0] for call in insert_calls]

    assert "aws_account_id" in sql
    assert {row[0] for row in rows} == {"123456789012"}
    assert {row[1] for row in rows} == {date(2026, 7, 27)}
    assert [row[3] for row in rows] == [12.34, 0.0, -4.2]


def test_insert_mock_data_uses_synthetic_account_id():
    clickhouse = Mock()

    collector.insert_mock_data(clickhouse)

    sql, rows = clickhouse.execute.call_args.args
    assert "aws_account_id" in sql
    assert {row[0] for row in rows} == {"000000000000"}
    assert all(isinstance(row[1], date) for row in rows)
