import normalizer
import pytest


def test_main_runs_exactly_one_successful_cycle(monkeypatch):
    calls = []
    monkeypatch.setattr(normalizer, "normalize", lambda: calls.append("cycle"))

    assert normalizer.main() == 0
    assert calls == ["cycle"]


def test_main_returns_nonzero_for_irrecoverable_failure(monkeypatch):
    def fail():
        raise OSError("ClickHouse down")

    monkeypatch.setattr(normalizer, "normalize", fail)

    assert normalizer.main() == 1


def test_normalize_waits_for_mutation(monkeypatch):
    executions = []

    class RecordingClient:
        def __init__(self, **_kwargs):
            pass

        def execute(self, query, **kwargs):
            executions.append((query, kwargs))

    monkeypatch.setattr(normalizer, "Client", RecordingClient)

    normalizer.normalize()

    assert len(executions) == 1
    query, options = executions[0]
    assert "ALTER TABLE costs UPDATE" in query
    assert options == {"settings": {"mutations_sync": 1}}


def test_normalize_propagates_database_failure(monkeypatch):
    class FailingClient:
        def __init__(self, **_kwargs):
            pass

        def execute(self, _query, **_kwargs):
            raise OSError("mutation failed")

    monkeypatch.setattr(normalizer, "Client", FailingClient)

    with pytest.raises(OSError, match="mutation failed"):
        normalizer.normalize()
