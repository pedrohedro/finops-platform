import os
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import boto3

app = FastAPI(title="FinOps API")

class AWSAccount(BaseModel):
    name: str
    aws_account_id: str
    role_arn: str

class AccountResponse(BaseModel):
    id: int
    name: str
    aws_account_id: str
    role_arn: str
    status: str
    last_sync: str | None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def get_db() -> Client | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Supabase connection error: {e}")
        return None

# ---------- Health ----------
@app.get("/api/health")
def health():
    db = get_db()
    db_status = "online" if db else "offline"
    mode = "production" if db else "demo/mock"

    aws_status = "configured" if os.getenv("AWS_ACCESS_KEY_ID") else "unconfigured"

    return {
        "status": "ok",
        "mode": mode,
        "database": db_status,
        "aws": aws_status,
        "version": "0.2.0"
    }

# ---------- Summary ----------
@app.get("/api/summary")
def get_summary(days: int = 30):
    db = get_db()
    if not db:
        return {"total_cost": 14580.42, "previous_cost": 13200.15}

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    prev_start = start_date - timedelta(days=days)

    current = db.table("costs").select("cost").gte("date", str(start_date)).lte("date", str(end_date)).eq("type", "actual").execute()
    previous = db.table("costs").select("cost").gte("date", str(prev_start)).lt("date", str(start_date)).eq("type", "actual").execute()

    total = sum(float(r["cost"]) for r in current.data) if current.data else 0
    prev_total = sum(float(r["cost"]) for r in previous.data) if previous.data else 0

    return {"total_cost": round(total, 2), "previous_cost": round(prev_total, 2)}

# ---------- Top Services ----------
@app.get("/api/services")
def top_services(days: int = 30, limit: int = 5):
    db = get_db()
    if not db:
        return [
            {"name": "EC2", "cost": 5200.50},
            {"name": "RDS", "cost": 3100.20},
            {"name": "S3", "cost": 1200.80},
            {"name": "Lambda", "cost": 850.30},
            {"name": "CloudFront", "cost": 420.10}
        ]

    start_date = str((datetime.now() - timedelta(days=days)).date())
    rows = db.table("costs").select("service, cost").gte("date", start_date).eq("type", "actual").execute()

    from collections import defaultdict
    totals = defaultdict(float)
    for r in rows.data:
        totals[r["service"]] += float(r["cost"])

    sorted_services = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [{"name": s, "cost": round(c, 2)} for s, c in sorted_services]

# ---------- Daily Trend ----------
@app.get("/api/daily")
def daily_trend(days: int = 30):
    db = get_db()
    if not db:
        return _generate_mock_daily(days)

    start_date = str((datetime.now() - timedelta(days=days)).date())
    rows = db.table("costs").select("date, cost, type").gte("date", start_date).order("date").execute()

    from collections import defaultdict
    grouped = defaultdict(lambda: defaultdict(float))
    for r in rows.data:
        grouped[r["date"]][r["type"]] += float(r["cost"])

    data = []
    for date in sorted(grouped.keys()):
        for record_type, cost in grouped[date].items():
            data.append({"date": date, "cost": round(cost, 2), "type": record_type})
    return data

# ---------- Environment Breakdown ----------
@app.get("/api/breakdown")
def environment_breakdown(days: int = 30):
    db = get_db()
    if not db:
        return [
            {"name": "Production", "cost": 8500.00},
            {"name": "Staging", "cost": 3200.50},
            {"name": "Development", "cost": 2880.00}
        ]

    start_date = str((datetime.now() - timedelta(days=days)).date())
    rows = db.table("costs").select("environment, cost").gte("date", start_date).eq("type", "actual").execute()

    from collections import defaultdict
    totals = defaultdict(float)
    for r in rows.data:
        totals[r["environment"] or "Unknown"] += float(r["cost"])

    sorted_envs = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    return [{"name": e, "cost": round(c, 2)} for e, c in sorted_envs]

# ---------- Team Breakdown ----------
@app.get("/api/teams")
def team_breakdown(days: int = 30):
    db = get_db()
    if not db:
        return [
            {"name": "Platform", "cost": 6500.00},
            {"name": "Data Science", "cost": 4200.00},
            {"name": "E-commerce", "cost": 3880.42}
        ]

    start_date = str((datetime.now() - timedelta(days=days)).date())
    rows = db.table("costs").select("team, cost").gte("date", start_date).eq("type", "actual").execute()

    from collections import defaultdict
    totals = defaultdict(float)
    for r in rows.data:
        totals[r["team"] or "Unassigned"] += float(r["cost"])

    sorted_teams = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    return [{"name": t, "cost": round(c, 2)} for t, c in sorted_teams]

# ---------- Raw Details ----------
@app.get("/api/details")
def raw_details(days: int = 7, limit: int = 100):
    db = get_db()
    if not db:
        import random
        services = ["EC2", "RDS", "S3", "Lambda"]
        teams = ["Platform", "Data Science", "E-commerce"]
        envs = ["Production", "Staging", "Dev"]
        return [
            {
                "date": (datetime.now() - timedelta(days=random.randint(0, days))).strftime("%Y-%m-%d"),
                "service": random.choice(services),
                "team": random.choice(teams),
                "environment": random.choice(envs),
                "cost": round(random.uniform(10, 500), 2),
                "type": "actual"
            } for _ in range(20)
        ]

    start_date = str((datetime.now() - timedelta(days=days)).date())
    rows = db.table("costs").select("date, service, team, environment, cost, type").gte("date", start_date).order("date", desc=True).order("cost", desc=True).limit(limit).execute()

    return [
        {
            "date": r["date"],
            "service": r["service"],
            "team": r["team"] or "Unassigned",
            "environment": r["environment"] or "Unknown",
            "cost": round(float(r["cost"]), 2),
            "type": r["type"]
        }
        for r in rows.data
    ]

# ---------- Account Management ----------
@app.get("/api/accounts")
def list_accounts():
    db = get_db()
    if not db:
        return []
    rows = db.table("accounts").select("*").execute()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "aws_account_id": r["account_id"],
            "role_arn": r["role_arn"],
            "status": r["status"],
            "last_sync": str(r["last_sync"]) if r["last_sync"] else None
        }
        for r in rows.data
    ]

@app.post("/api/accounts")
def create_account(account: AWSAccount):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database unavailable")

    result = db.table("accounts").insert({
        "name": account.name,
        "account_id": account.aws_account_id,
        "role_arn": account.role_arn,
        "status": "active"
    }).execute()

    if result.data:
        return {"status": "created", "id": result.data[0]["id"]}
    raise HTTPException(status_code=500, detail="Failed to create account")

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

# ---------- Helpers ----------
def _generate_mock_daily(days: int):
    import random
    data = []
    end_date = datetime.now()
    for i in range(days):
        date = (end_date - timedelta(days=days - i)).strftime("%Y-%m-%d")
        cost = 450 + (i * 2) + random.uniform(-50, 50)
        data.append({"date": date, "cost": round(cost, 2), "type": "actual"})
        if i > days - 7:
            f_date = (end_date + timedelta(days=i - (days - 7))).strftime("%Y-%m-%d")
            data.append({"date": f_date, "cost": round(cost * 1.05, 2), "type": "forecast"})
    return data
