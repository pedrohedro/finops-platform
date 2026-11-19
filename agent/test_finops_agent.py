from datetime import date, datetime, timezone
from types import SimpleNamespace

import httpx
import pytest

import finops_agent
from finops_agent import (
    TOOLS,
    BudgetExceeded,
    DailyTokenBudget,
    FinOpsAgent,
    ToolInputError,
    _route,
    make_http_tool_executor,
)


def text(value):
    return SimpleNamespace(type="text", text=value)


def tool_use(block_id, name, args):
    return SimpleNamespace(type="tool_use", id=block_id, name=name, input=args)


def response(stop_reason, content, input_tokens=10, output_tokens=5):
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=content,
        model="claude-opus-5-5",
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        # Snapshot messages: the agent keeps appending to the same list.
        self.calls.append({**kwargs, "messages": list(kwargs["messages"])})
        return self.responses.pop(0)


def make_agent(responses, execute_tool=None, budget=None, max_iterations=6):
    client = FakeClient(responses)
    agent = FinOpsAgent(
        client=client,
        execute_tool=execute_tool or (lambda name, args: '{"total_cost": 1.0}'),
        budget=budget or DailyTokenBudget(1_000_000),
        max_iterations=max_iterations,
    )
    return agent, client


def test_tools_are_strict_read_only_schemas():
    for tool in TOOLS:
        schema = tool["input_schema"]
        assert tool["strict"] is True
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"])


def test_answers_without_tools():
    agent, client = make_agent([response("end_turn", [text("Tudo certo.")])])
    result = agent.run([{"role": "user", "content": "oi"}], request_id="r1")
    assert result.reply == "Tudo certo."
    assert result.tool_calls == []
    request = client.calls[0]
    assert request["model"] == "claude-opus-5-5"
    assert request["thinking"] == {"type": "adaptive"}
    assert request["fallbacks"] == "default"
    assert request["betas"] == ["server-side-fallback-2026-07-01"]
    assert "tool_choice" not in request


def test_runs_tool_loop_and_keeps_history_append_only():
    first = [text("Vou consultar."), tool_use("t1", "get_cost_summary", {"days": 30})]
    seen = []

    def execute(name, args):
        seen.append((name, args))
        return '{"total_cost": 120.5, "previous_cost": 100.0}'

    agent, client = make_agent(
        [response("tool_use", first), response("end_turn", [text("Gastou US$ 120.50.")])],
        execute_tool=execute,
    )
    result = agent.run([{"role": "user", "content": "quanto gastei?"}], request_id="r2")

    assert seen == [("get_cost_summary", {"days": 30})]
    assert result.reply == "Gastou US$ 120.50."
    assert result.tool_calls == [{"tool": "get_cost_summary", "status": "ok"}]
    assert result.input_tokens == 20 and result.output_tokens == 10

    second_messages = client.calls[1]["messages"]
    assert second_messages[0] == {"role": "user", "content": "quanto gastei?"}
    assert second_messages[1] == {"role": "assistant", "content": first}
    assert second_messages[2]["content"] == [
        {
            "type": "tool_result",
            "tool_use_id": "t1",
            "content": '{"total_cost": 120.5, "previous_cost": 100.0}',
        }
    ]


def test_parallel_tool_results_return_in_one_message():
    calls = [
        tool_use("a", "get_cost_summary", {"days": 7}),
        tool_use("b", "get_top_services", {"days": 7, "limit": 3}),
    ]
    agent, client = make_agent(
        [response("tool_use", calls), response("end_turn", [text("ok")])]
    )
    agent.run([{"role": "user", "content": "x"}], request_id="r3")
    results = client.calls[1]["messages"][2]["content"]
    assert [r["tool_use_id"] for r in results] == ["a", "b"]


def test_invalid_tool_input_becomes_error_result():
    bad = [tool_use("t1", "get_cost_summary", {"days": 9999})]
    agent, client = make_agent([response("tool_use", bad), response("end_turn", [text("ok")])])
    result = agent.run([{"role": "user", "content": "x"}], request_id="r4")
    tool_result = client.calls[1]["messages"][2]["content"][0]
    assert tool_result["is_error"] is True
    assert result.tool_calls == [{"tool": "get_cost_summary", "status": "invalid_input"}]


def test_upstream_failure_becomes_error_result():
    def execute(name, args):
        raise httpx.ConnectError("down")

    calls = [tool_use("t1", "get_daily_trend", {"days": 7})]
    agent, client = make_agent(
        [response("tool_use", calls), response("end_turn", [text("sem dados")])],
        execute_tool=execute,
    )
    result = agent.run([{"role": "user", "content": "x"}], request_id="r5")
    assert client.calls[1]["messages"][2]["content"][0]["is_error"] is True
    assert result.tool_calls[0]["status"] == "unavailable"


def test_refusal_returns_safe_message():
    agent, _ = make_agent([response("refusal", [])])
    result = agent.run([{"role": "user", "content": "x"}], request_id="r6")
    assert result.stop_reason == "refusal"
    assert "Não posso ajudar" in result.reply


def test_iteration_cap_stops_runaway_loop():
    loop = [tool_use("t", "get_cost_summary", {"days": 1})]
    agent, client = make_agent(
        [response("tool_use", loop) for _ in range(3)], max_iterations=3
    )
    result = agent.run([{"role": "user", "content": "x"}], request_id="r7")
    assert result.stop_reason == "max_iterations"
    assert len(client.calls) == 3


def test_budget_blocks_calls_once_spent():
    budget = DailyTokenBudget(limit=15)
    agent, client = make_agent(
        [response("end_turn", [text("a")]), response("end_turn", [text("b")])],
        budget=budget,
    )
    agent.run([{"role": "user", "content": "x"}], request_id="r8")
    assert budget.used == 15
    with pytest.raises(BudgetExceeded):
        agent.run([{"role": "user", "content": "y"}], request_id="r9")
    assert len(client.calls) == 1


def test_budget_resets_next_day():
    now = {"value": datetime(2026, 11, 19, 23, 0, tzinfo=timezone.utc)}
    budget = DailyTokenBudget(limit=10, clock=lambda: now["value"])
    budget.add(10)
    with pytest.raises(BudgetExceeded):
        budget.check()
    now["value"] = datetime(2026, 11, 20, 0, 1, tzinfo=timezone.utc)
    budget.check()
    assert budget.used == 0


@pytest.mark.parametrize(
    "name,args,expected",
    [
        ("get_cost_summary", {"days": 30}, ("/api/summary", {"days": 30})),
        ("get_top_services", {"days": 7, "limit": 5}, ("/api/services", {"days": 7, "limit": 5})),
        ("get_daily_trend", {"days": 90}, ("/api/daily", {"days": 90})),
        ("get_cost_breakdown", {"dimension": "team", "days": 30}, ("/api/teams", {"days": 30})),
        (
            "get_cost_breakdown",
            {"dimension": "environment", "days": 30},
            ("/api/breakdown", {"days": 30}),
        ),
        ("get_cost_details", {"days": 7, "limit": 50}, ("/api/details", {"days": 7, "limit": 50})),
    ],
)
def test_routes_are_allowlisted(name, args, expected):
    assert _route(name, args) == expected


@pytest.mark.parametrize(
    "name,args",
    [
        ("get_cost_summary", {"days": 0}),
        ("get_cost_summary", {"days": True}),
        ("get_cost_summary", {"days": "30"}),
        ("get_top_services", {"days": 7, "limit": 1000}),
        ("get_cost_breakdown", {"dimension": "service", "days": 7}),
        ("create_account", {}),
        ("get_cost_summary", "days=30"),
    ],
)
def test_routes_reject_bad_input(name, args):
    with pytest.raises(ToolInputError):
        _route(name, args)


def test_http_executor_calls_api_and_truncates(monkeypatch):
    monkeypatch.setattr(finops_agent, "MAX_TOOL_RESULT_CHARS", 30)
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=[{"name": "EC2", "cost": 1.0}] * 10)

    client = httpx.Client(base_url="http://api.test", transport=httpx.MockTransport(handler))
    execute = make_http_tool_executor(client)
    output = execute("get_top_services", {"days": 7, "limit": 10})
    assert requests[0].method == "GET"
    assert str(requests[0].url) == "http://api.test/api/services?days=7&limit=10"
    assert output.endswith("[resultado truncado]")


def test_http_executor_surfaces_status_errors():
    client = httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(lambda request: httpx.Response(503)),
    )
    with pytest.raises(httpx.HTTPStatusError):
        make_http_tool_executor(client)("get_cost_summary", {"days": 7})


def test_each_call_gets_the_remaining_deadline():
    now = {"t": 0.0}
    agent, client = make_agent(
        [response("tool_use", [tool_use("t", "get_cost_summary", {"days": 1})]),
         response("end_turn", [text("ok")])],
    )
    agent.deadline_seconds = 100
    agent._clock = lambda: now["t"]

    def execute(name, args):
        now["t"] += 40  # a slow tool round eats into the turn's deadline
        return "{}"

    agent.execute_tool = execute
    agent.run([{"role": "user", "content": "x"}], request_id="d1")
    assert client.calls[0]["timeout"] == 50
    assert client.calls[1]["timeout"] == 30


def test_deadline_stops_before_another_model_call():
    now = {"t": 0.0}
    agent, client = make_agent(
        [response("tool_use", [tool_use("t", "get_cost_summary", {"days": 1})])]
    )
    agent.deadline_seconds = 10
    agent._clock = lambda: now["t"]

    def execute(name, args):
        now["t"] += 8
        return "{}"

    agent.execute_tool = execute
    result = agent.run([{"role": "user", "content": "x"}], request_id="d2")
    assert result.stop_reason == "deadline"
    assert len(client.calls) == 1


def test_long_reply_is_capped_to_history_limit():
    agent, _ = make_agent([response("end_turn", [text("a" * 50_000)])])
    result = agent.run([{"role": "user", "content": "x"}], request_id="d3")
    assert len(result.reply) <= finops_agent.MAX_REPLY_CHARS
    assert result.reply.endswith("[resposta truncada]")
