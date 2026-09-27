import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth.account_router import get_current_context
from database.db import get_db
from database.models.cloud_account import CloudAccount
from database.models.project import Project

router = APIRouter(
    prefix="/api/intelligence",
    tags=["Intelligence"],
)

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"


def read_json(filename: str, default):
    path = DATA_DIR / filename

    if not path.exists():
        return default

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return default


@router.get("/overview")
def intelligence_overview(
    context: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    organization_id = context["organization_id"]

    project_count = (
        db.query(func.count(Project.id))
        .filter(Project.organization_id == organization_id)
        .scalar()
        or 0
    )

    cloud_account_count = (
        db.query(func.count(CloudAccount.id))
        .filter(CloudAccount.organization_id == organization_id)
        .scalar()
        or 0
    )

    cost_data = read_json("cost_data.json", {})
    causal_chain = read_json("causal_chain.json", {})
    causal_candidates = read_json("causal_candidates.json", [])
    anomaly_scores = read_json("anomaly_scores.json", {})

    services = cost_data.get("services", {})

    total_cost_increase = cost_data.get(
        "total_cost_increase",
        sum(
            service.get("cost_increase", 0)
            for service in services.values()
        ),
    )

    affected_services = sum(
        1
        for service in services.values()
        if service.get("cost_increase", 0) > 0
    )

    return {
        "organization_id": organization_id,
        "projects": project_count,
        "cloud_accounts": cloud_account_count,
        "total_cost_increase": total_cost_increase,
        "currency": cost_data.get("currency", "USD"),
        "affected_services": affected_services,
        "causal_candidate_count": len(causal_candidates),
        "candidate_root_cause": causal_chain.get(
            "candidate_root_cause"
        ),
        "causal_chain": causal_chain.get(
            "causal_chain",
            [],
        ),
        "analysis_status": "available",
        "data_source": "local-analysis",
    }


@router.get("/cost")
def intelligence_cost(
    context: dict = Depends(get_current_context),
):
    return read_json("cost_data.json", {})


@router.get("/causal")
def intelligence_causal(
    context: dict = Depends(get_current_context),
):
    return {
        "chain": read_json("causal_chain.json", {}),
        "candidates": read_json(
            "causal_candidates.json",
            [],
        ),
    }


@router.get("/anomalies")
def intelligence_anomalies(
    context: dict = Depends(get_current_context),
):
    return read_json("anomaly_scores.json", {})
