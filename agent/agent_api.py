"""Internal HTTP service for the FinOps agent.

Listens on loopback only (supervisord) or on the private Compose network. The
dashboard never calls it directly: the FinOps API proxies /api/agent/chat here.
"""

from __future__ import annotations

import logging
import os
import threading
from functools import lru_cache
from typing import Annotated, Literal
from uuid import uuid4

import anthropic
from fastapi import FastAPI, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from pydantic import BaseModel, Field, ValidationInfo, field_validator
from starlette.responses import Response

from finops_agent import BudgetExceeded, FinOpsAgent, build_default_agent

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("finops_agent.api")

MAX_CONCURRENCY = int(os.getenv("AGENT_MAX_CONCURRENCY", "4"))

app = FastAPI(title="FinOps Agent", docs_url=None, redoc_url=None, openapi_url=None)

CHAT_REQUESTS = Counter(
    "finops_agent_chat_requests_total", "Agent chat requests by outcome", ["outcome"]
)
TOKENS = Counter("finops_agent_tokens_total", "Tokens spent by the agent", ["direction"])
TOOL_CALLS = Counter(
    "finops_agent_tool_calls_total", "Agent tool calls", ["tool", "status"]
)

_slots = threading.BoundedSemaphore(MAX_CONCURRENCY)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    # Assistant turns echo model replies (capped at 20k chars by the agent);
    # user turns are capped at 4k.
    content: Annotated[str, Field(min_length=1, max_length=20000)]

    @field_validator("content")
    @classmethod
    def user_turn_size(cls, content: str, info: ValidationInfo) -> str:
        if info.data.get("role") == "user" and len(content) > 4000:
            raise ValueError("user messages are limited to 4000 characters")
        return content


class ChatRequest(BaseModel):
    messages: Annotated[list[ChatMessage], Field(min_length=1, max_length=20)]

    @field_validator("messages")
    @classmethod
    def alternating_turns(cls, messages: list[ChatMessage]) -> list[ChatMessage]:
        for index, message in enumerate(messages):
            expected = "user" if index % 2 == 0 else "assistant"
            if message.role != expected:
                raise ValueError("turns must alternate, starting and ending with user")
        if messages[-1].role != "user":
            raise ValueError("the last turn must come from the user")
        return messages


class ChatResponse(BaseModel):
    reply: str
    request_id: str
    model: str
    tool_calls: list[dict]


def agent_configured() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))


@lru_cache(maxsize=1)
def get_agent() -> FinOpsAgent:
    return build_default_agent()


@app.get("/healthz")
def liveness():
    return {"status": "ok"}


@app.get("/readyz")
def readiness():
    if not agent_configured():
        raise HTTPException(status_code=503, detail="agent not configured")
    return {"status": "ready"}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not agent_configured():
        CHAT_REQUESTS.labels("not_configured").inc()
        raise HTTPException(status_code=503, detail="agent not configured")
    if not _slots.acquire(blocking=False):
        CHAT_REQUESTS.labels("busy").inc()
        raise HTTPException(status_code=429, detail="agent busy, try again shortly")

    request_id = str(uuid4())
    try:
        result = get_agent().run(
            [m.model_dump() for m in request.messages], request_id=request_id
        )
    except BudgetExceeded:
        CHAT_REQUESTS.labels("budget_exceeded").inc()
        raise HTTPException(status_code=429, detail="daily agent budget exhausted")
    except anthropic.RateLimitError:
        CHAT_REQUESTS.labels("rate_limited").inc()
        raise HTTPException(status_code=429, detail="model rate limited, try again shortly")
    except anthropic.AuthenticationError:
        logger.error("Anthropic credentials rejected")
        CHAT_REQUESTS.labels("auth_error").inc()
        raise HTTPException(status_code=503, detail="agent not configured")
    except (anthropic.APIStatusError, anthropic.APIConnectionError):
        logger.exception("Model call failed request_id=%s", request_id)
        CHAT_REQUESTS.labels("upstream_error").inc()
        raise HTTPException(status_code=502, detail="model unavailable")
    finally:
        _slots.release()

    TOKENS.labels("input").inc(result.input_tokens)
    TOKENS.labels("output").inc(result.output_tokens)
    for call in result.tool_calls:
        TOOL_CALLS.labels(call["tool"], call["status"]).inc()
    CHAT_REQUESTS.labels(result.stop_reason or "unknown").inc()
    logger.info(
        "agent_turn request_id=%s stop=%s tools=%d in=%d out=%d",
        request_id,
        result.stop_reason,
        len(result.tool_calls),
        result.input_tokens,
        result.output_tokens,
    )
    return ChatResponse(
        reply=result.reply,
        request_id=request_id,
        model=result.model,
        tool_calls=result.tool_calls,
    )
