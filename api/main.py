import logging
import os
from datetime import datetime, timedelta
from time import perf_counter
from typing import Annotated
from uuid import uuid4

import boto3
from clickhouse_driver import Client
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


def get_db() -> Client:
    return Client(
        host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
        port=int(os.getenv("CLICKHOUSE_PORT", "9000")),
        database=os.getenv("CLICKHOUSE_DB", "finops"),
        user=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
    )


def execute_query(query: str, params: object | None = None) -> list[tuple]:
    try:
        return get_db().execute(query, params or {})
    except Exception as exc:
        logger.exception("ClickHouse query failed")
        raise HTTPException(status_code=503, detail="ClickHouse unavailable") from exc


app = FastAPI(title="FinOps API")

HTTP_REQUESTS = Counter(
    "finops_api_http_requests_total",
    "Total HTTP requests handled by the FinOps API",
    ["method", "path", "status"],
)
HTTP_LATENCY = Histogram(
    "finops_api_http_request_duration_seconds",
    "FinOps API request duration in seconds",
    ["method", "path"],
)

Days = Annotated[int, Query(ge=1, le=365)]
Limit = Annotated[int, Query(ge=1, le=1000)]


class AWSAccount(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    aws_account_id: Annotated[str, Field(pattern=r"^\d{12}$")]
    role_arn: Annotated[
        str,
        Field(pattern=r"^arn:aws:iam::\d{12}:role/[A-Za-z0-9+=,.@_/-]{1,512}$"),
    ]

class AccountResponse(BaseModel):
    id: str
    name: str
    aws_account_id: str
    role_arn: str
    status: str
    last_sync: str | None

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def observe_http(request: Request, call_next):
    started = perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)
    HTTP_REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    HTTP_LATENCY.labels(request.method, path).observe(perf_counter() - started)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ---------- Health ----------
def database_online() -> bool:
    try:
        get_db().execute("SELECT 1")
        return True
    except Exception:
        return False


@app.get("/healthz")
def liveness():
    return {"status": "ok"}


@app.get("/readyz")
def readiness():
    if not database_online():
        raise HTTPException(status_code=503, detail="ClickHouse unavailable")
    return {"status": "ready", "database": "online"}


@app.get("/api/health")
def health():
    online = database_online()
    return {
        "status": "ok" if online else "degraded",
        "mode": "clickhouse",
        "database": "online" if online else "offline",
        "aws": "configured" if os.getenv("AWS_ACCESS_KEY_ID") else "unconfigured",
        "version": "0.2.0",
    }

# ---------- Summary ----------
@app.get("/api/summary")
def get_summary(days: Days = 30):
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    previous_start = start_date - timedelta(days=days)
    rows = execute_query(
        """
        SELECT
            round(sumIf(cost, record_type = 'actual' AND date >= %(start)s AND date <= %(end)s), 2),
            round(sumIf(cost, record_type = 'actual' AND date >= %(previous_start)s AND date < %(start)s), 2)
        FROM costs
        """,
        {"start": start_date, "end": end_date, "previous_start": previous_start},
    )
    current, previous = rows[0]
    return {"total_cost": float(current), "previous_cost": float(previous)}

# ---------- Top Services ----------
@app.get("/api/services")
def top_services(days: Days = 30, limit: Limit = 5):
    rows = execute_query(
        """
        SELECT service, round(sum(cost), 2) AS total
        FROM costs
        WHERE date >= %(start)s AND record_type = 'actual'
        GROUP BY service
        ORDER BY total DESC
        LIMIT %(limit)s
        """,
        {"start": datetime.now().date() - timedelta(days=days), "limit": limit},
    )
    return [{"name": service, "cost": float(cost)} for service, cost in rows]

# ---------- Daily Trend ----------
@app.get("/api/daily")
def daily_trend(days: Days = 30):
    rows = execute_query(
        """
        SELECT toString(date), round(sum(cost), 2), record_type
        FROM costs
        WHERE date >= %(start)s
        GROUP BY date, record_type
        ORDER BY date, record_type
        """,
        {"start": datetime.now().date() - timedelta(days=days)},
    )
    return [
        {"date": date, "cost": float(cost), "type": record_type}
        for date, cost, record_type in rows
    ]


def grouped_costs(column: str, days: int, unknown: str) -> list[dict]:
    if column not in {"environment", "team"}:
        raise ValueError("Unsupported grouping column")
    rows = execute_query(
        f"""
        SELECT if({column} = '', %(unknown)s, {column}) AS name, round(sum(cost), 2)
        FROM costs
        WHERE date >= %(start)s AND record_type = 'actual'
        GROUP BY name
        ORDER BY sum(cost) DESC
        """,
        {"start": datetime.now().date() - timedelta(days=days), "unknown": unknown},
    )
    return [{"name": name, "cost": float(cost)} for name, cost in rows]

# ---------- Environment Breakdown ----------
@app.get("/api/breakdown")
def environment_breakdown(days: Days = 30):
    return grouped_costs("environment", days, "Unknown")

# ---------- Team Breakdown ----------
@app.get("/api/teams")
def team_breakdown(days: Days = 30):
    return grouped_costs("team", days, "Unassigned")

# ---------- Raw Details ----------
@app.get("/api/details")
def raw_details(days: Days = 7, limit: Limit = 100):
    rows = execute_query(
        """
        SELECT
            toString(date),
            service,
            if(team = '', 'Unassigned', team),
            if(environment = '', 'Unknown', environment),
            round(cost, 2),
            record_type
        FROM costs
        WHERE date >= %(start)s
        ORDER BY date DESC, cost DESC
        LIMIT %(limit)s
        """,
        {"start": datetime.now().date() - timedelta(days=days), "limit": limit},
    )
    return [
        {
            "date": date,
            "service": service,
            "team": team,
            "environment": environment,
            "cost": float(cost),
            "type": record_type,
        }
        for date, service, team, environment, cost, record_type in rows
    ]

# ---------- Account Management ----------
@app.get("/api/accounts")
def list_accounts():
    rows = execute_query(
        """
        SELECT
            toString(id), name, aws_account_id, role_arn, status, toString(last_sync)
        FROM accounts
        ORDER BY created_at DESC
        """
    )
    return [
        {
            "id": account_id,
            "name": name,
            "aws_account_id": aws_account_id,
            "role_arn": role_arn,
            "status": status,
            "last_sync": last_sync,
        }
        for account_id, name, aws_account_id, role_arn, status, last_sync in rows
    ]

@app.post("/api/accounts")
def create_account(account: AWSAccount):
    account_id = uuid4()
    execute_query(
        """
        INSERT INTO accounts (id, name, aws_account_id, role_arn, status)
        VALUES
        """,
        [
            (
                account_id,
                account.name,
                account.aws_account_id,
                account.role_arn,
                "active",
            )
        ],
    )
    return {"status": "created", "id": str(account_id)}

@app.post("/api/accounts/test")
def test_account_connection(account: AWSAccount):
    try:
        sts = boto3.client("sts")
        response = sts.assume_role(
            RoleArn=account.role_arn,
            RoleSessionName="finops-connection-test",
            DurationSeconds=900
        )
        return {
            "status": "success",
            "message": f"Connected to account {account.aws_account_id}",
            "assumed_role": response["AssumedRoleUser"]["Arn"]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
