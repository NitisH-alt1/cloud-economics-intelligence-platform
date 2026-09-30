import json
import math
from datetime import date, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.dependencies import get_current_context
from analyzer.cost.cost_model import calculate_cost_increase, cost_anomaly_score
from database.db import get_db
from database.models.cloud_account import CloudAccount
from database.models.cost_record import CostRecord
from database.models.project import Project, project_cloud_accounts

router = APIRouter(prefix="/api", tags=["Project Intelligence"])
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SERVICES = ("checkout", "inventory", "payment")


def _json(name, default):
    try:
        return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _finite_number(value):
    try:
        number = float(value)
        return number if math.isfinite(number) and number >= 0 else 0.0
    except (TypeError, ValueError):
        return 0.0


def _project(project_id: str, context: dict, db: Session) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.organization_id == context["organization_id"]))
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


def _ensure_demo_records(project: Project, db: Session):
    # Cost, causal, anomaly, and recommendation endpoints can request the demo
    # series at the same time. Serialize first-time seeding per project so
    # concurrent PostgreSQL requests do not insert the same unique periods.
    locked_project_id = db.scalar(
        select(Project.id)
        .where(
            Project.id == project.id,
            Project.organization_id == project.organization_id,
        )
        .with_for_update()
    )
    if locked_project_id is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    accounts = db.execute(select(CloudAccount).join(project_cloud_accounts, CloudAccount.id == project_cloud_accounts.c.cloud_account_id).where(project_cloud_accounts.c.project_id == project.id, CloudAccount.organization_id == project.organization_id).order_by(CloudAccount.created_at)).scalars().all()
    targets = accounts or [None]
    if accounts:
        db.query(CostRecord).filter(
            CostRecord.organization_id == project.organization_id,
            CostRecord.project_id == project.id,
            CostRecord.cloud_account_id.is_(None),
            CostRecord.source == "local-demo",
        ).delete(synchronize_session=False)
        db.flush()
    # Store 60 days of reproducible demo estimates. Dates roll with the current
    # day; service weights repeat deterministically for every project/account.
    end = date.today()
    start = end - timedelta(days=59)
    sample_data = _json("cost_data.json", {})
    sample_services = sample_data.get("services", {}) if isinstance(sample_data, dict) else {}
    if not isinstance(sample_services, dict):
        sample_services = {}
    existing = set(db.execute(select(CostRecord.usage_date, CostRecord.service, CostRecord.cloud_account_id).where(CostRecord.organization_id == project.organization_id, CostRecord.project_id == project.id)).all())
    rows = []
    for offset in range(60):
        day = start + timedelta(days=offset)
        recent = offset >= 30
        for service in SERVICES:
            sample = sample_services.get(service, {})
            monthly = _finite_number(sample.get("current_cost" if recent else "baseline_cost"))
            weekend_factor = 0.92 if day.weekday() >= 5 else 1.0
            base_daily = round(monthly / 30.0 * weekend_factor, 4)
            account_share = round(base_daily / len(targets), 4)
            for account_index, account in enumerate(targets):
                if (day, service, account.id if account else None) in existing:
                    continue
                # Assign any rounding remainder to the last linked account so
                # the daily project estimate stays unchanged as accounts vary.
                daily = account_share if account_index < len(targets) - 1 else round(
                    base_daily - account_share * (len(targets) - 1), 4
                )
                rows.append(CostRecord(organization_id=project.organization_id, project_id=project.id, cloud_account_id=account.id if account else None, provider=account.provider if account else "local", service=service, usage_date=day, cost=daily, currency="USD", usage_quantity=round(daily * 100, 2), source="local-demo", environment="demo", metadata_json={"basis": "deterministic resource estimate", "account_name": account.display_name if account else None}))
    if rows:
        db.add_all(rows)
        db.commit()


def _records(project: Project, db: Session):
    _ensure_demo_records(project, db)
    return db.scalars(select(CostRecord).where(CostRecord.organization_id == project.organization_id, CostRecord.project_id == project.id).order_by(CostRecord.usage_date, CostRecord.service)).all()


def _cost_payload(project: Project, records: list[CostRecord]):
    end = date.today()
    current_start, previous_start = end - timedelta(days=29), end - timedelta(days=59)
    current, previous = {}, {}
    trend, providers, accounts = {}, {}, {}
    for row in records:
        if row.usage_date < previous_start:
            continue
        bucket = current if row.usage_date >= current_start else previous
        bucket[row.service] = bucket.get(row.service, 0.0) + row.cost
        day = row.usage_date.isoformat()
        trend[day] = trend.get(day, 0.0) + row.cost
        if row.usage_date >= current_start:
            providers[row.provider] = providers.get(row.provider, 0.0) + row.cost
            metadata = row.metadata_json if isinstance(row.metadata_json, dict) else {}
            key = metadata.get("account_name") or "Unassigned demo account"
            accounts[key] = accounts.get(key, 0.0) + row.cost
    current_total, previous_total = sum(current.values()), sum(previous.values())
    change = current_total - previous_total
    percent = (change / previous_total * 100) if previous_total else None
    names = set(current) | set(previous)
    breakdown = []
    for service in sorted(names):
        amount = current.get(service, 0.0)
        breakdown.append({"service": service, "current_cost": round(amount, 4), "previous_cost": round(previous.get(service, 0.0), 4), "change": round(amount - previous.get(service, 0.0), 4), "share": round(amount / current_total, 4) if current_total else None})
    return {"project_id": project.id, "source": "Local Demo Data", "currency": "USD", "period_days": 30, "previous_period_days": 30, "total_cost": round(current_total, 4), "previous_total_cost": round(previous_total, 4), "cost_change": round(change, 4), "percentage_change": round(percent, 2) if percent is not None else None, "services": breakdown, "trend": [{"date": day, "cost": round(value, 4)} for day, value in sorted(trend.items())], "providers": [{"provider": key, "cost": round(value, 4)} for key, value in sorted(providers.items())], "cloud_accounts": [{"account": key, "cost": round(value, 4)} for key, value in sorted(accounts.items())]}


def _legacy_cost_payload(payload):
    services = {}
    positive_increase = sum(max(0.0, item["change"]) for item in payload["services"])
    for item in payload["services"]:
        baseline = item["previous_cost"]
        current = item["current_cost"]
        increase = calculate_cost_increase(baseline, current)
        services[item["service"]] = {
            "baseline_cost": baseline,
            "current_cost": current,
            "cost_increase": increase,
            "cost_anomaly_score": cost_anomaly_score(baseline, current),
            "attribution_share": round(increase / positive_increase, 4) if positive_increase else 0.0,
        }
    return {"source": payload["source"], "currency": payload["currency"], "model": "Deterministic local demo period comparison", "total_cost_increase": round(positive_increase, 4), "services": services}


@router.get("/projects/{project_id}/cost")
def project_cost(project_id: str, context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    project = _project(project_id, context, db)
    return _cost_payload(project, _records(project, db))


@router.get("/projects/{project_id}/anomalies")
def project_anomalies(project_id: str, context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    project = _project(project_id, context, db)
    baseline = _json("baseline.json", {})
    observed = _json("failure.json", {})
    scores = _json("anomaly_scores.json", {})
    baseline = baseline if isinstance(baseline, dict) else {}
    observed = observed if isinstance(observed, dict) else {}
    scores = scores if isinstance(scores, dict) else {}
    results = []
    for service, metrics in scores.items():
        if not isinstance(metrics, dict):
            continue
        for metric, score in metrics.items():
            try:
                score = float(score)
                if not math.isfinite(score):
                    continue
            except (TypeError, ValueError):
                continue
            baseline_metrics = baseline.get(service, {})
            observed_metrics = observed.get(service, {})
            reference = baseline_metrics.get(metric) if isinstance(baseline_metrics, dict) else None
            value = observed_metrics.get(metric) if isinstance(observed_metrics, dict) else None
            results.append({"service": service, "metric": metric, "observed": value, "baseline": reference, "score": score, "severity": "high" if score >= 1 else "moderate" if score >= 0.25 else "low", "period": "Local demo failure scenario", "explanation": f"Observed {metric} differs from the local baseline for {service}.", "source": "Existing analyzer sample output"})
    return {"project_id": project.id, "source": "Local Demo Data", "anomalies": results}


@router.get("/projects/{project_id}/causal")
def project_causal(project_id: str, context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    project = _project(project_id, context, db)
    cost = _cost_payload(project, _records(project, db))
    attribution = {item["service"]: item["change"] for item in cost["services"]}
    chain = _json("causal_chain.json", {})
    candidates = _json("causal_candidates.json", [])
    chain = chain if isinstance(chain, dict) else {}
    candidates = candidates if isinstance(candidates, list) else []
    return {"project_id": project.id, "source": "Existing model-derived causal candidate sample", "label": "Model-derived causal candidates", "chain": chain, "candidates": candidates, "cost_attribution": [{"service": service, "estimated_change": round(amount, 4), "currency": "USD"} for service, amount in attribution.items()]}


@router.get("/projects/{project_id}/recommendations")
def project_recommendations(project_id: str, context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    project = _project(project_id, context, db)
    cost = _cost_payload(project, _records(project, db))
    anomalies = project_anomalies(project_id, context, db)["anomalies"]
    results = []
    for item in cost["services"]:
        if item["change"] > 0:
            results.append({"id": f"cost-{item['service']}", "title": f"Review {item['service']} cost increase", "description": "Compare the service's recent estimated cost with the previous demo period.", "affected_service": item["service"], "reason": "Estimated cost increased between periods.", "evidence": {"change": item["change"], "currency": cost["currency"], "source": cost["source"]}, "category": "cost", "severity": "high" if item["share"] and item["share"] > 0.4 else "moderate", "status": "open"})
    for item in anomalies:
        if item["severity"] in {"high", "moderate"}:
            results.append({"id": f"anomaly-{item['service']}-{item['metric']}", "title": f"Investigate {item['metric']} anomaly", "description": item["explanation"], "affected_service": item["service"], "reason": "The existing analyzer sample reports a deviation from baseline.", "evidence": {"score": item["score"], "observed": item["observed"], "baseline": item["baseline"]}, "category": "anomaly", "severity": item["severity"], "status": "open"})
    return {"project_id": project.id, "source": "Generated from Local Demo Data and existing analyzer sample output", "recommendations": results}


# Legacy routes remain authenticated and organization scoped; with no project,
# return an empty demonstration result instead of exposing shared samples.
def _first_project(context, db):
    return db.scalar(select(Project).where(Project.organization_id == context["organization_id"]).order_by(Project.created_at).limit(1))


@router.get("/intelligence/overview")
def intelligence_overview(context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    projects = db.scalars(select(Project).where(Project.organization_id == context["organization_id"]).order_by(Project.created_at, Project.id)).all()
    accounts = db.scalars(select(CloudAccount).where(CloudAccount.organization_id == context["organization_id"])).all()
    project = projects[0] if projects else None
    payload = _cost_payload(project, _records(project, db)) if project else None
    causal = project_causal(project.id, context, db) if project else {"candidates": []}
    chain = causal.get("chain", {})
    return {"organization_id": context["organization_id"], "projects": len(projects), "cloud_accounts": len(accounts), "total_cost": payload["total_cost"] if payload else None, "cost_change": payload["cost_change"] if payload else None, "total_cost_increase": sum(max(0.0, item["change"]) for item in payload["services"]) if payload else 0.0, "affected_services": sum(1 for item in payload["services"] if item["change"] > 0) if payload else 0, "currency": "USD", "causal_candidate_count": len(causal["candidates"]), "candidate_root_cause": chain.get("candidate_root_cause"), "causal_chain": chain.get("causal_chain", []), "analysis_status": "available" if project else "no-project", "data_source": "Local Demo Data", "project_id": project.id if project else None}


@router.get("/intelligence/cost")
def intelligence_cost(context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    project = _first_project(context, db)
    return _legacy_cost_payload(_cost_payload(project, _records(project, db))) if project else {"source": "Local Demo Data", "currency": "USD", "model": "Deterministic local demo period comparison", "total_cost_increase": 0.0, "services": {}}


@router.get("/intelligence/causal")
def intelligence_causal(context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    project = _first_project(context, db)
    return project_causal(project.id, context, db) if project else {"chain": {}, "candidates": [], "source": "Local Demo Data"}


@router.get("/intelligence/anomalies")
def intelligence_anomalies(context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    project = _first_project(context, db)
    if project is None:
        return {}
    # Keep the legacy service -> metric -> score shape. The newer project
    # endpoint provides observations, baselines, severity, and explanations.
    detailed = project_anomalies(project.id, context, db)["anomalies"]
    scores = {}
    for item in detailed:
        scores.setdefault(item["service"], {})[item["metric"]] = item["score"]
    return scores
