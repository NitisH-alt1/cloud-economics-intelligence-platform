from auth.cloud_router import router as cloud_router
from auth.connection_router import router as connection_router
from auth.intelligence_router import (
    router as intelligence_router,
    project_cost,
    project_causal,
    project_anomalies,
)
from auth.dependencies import get_current_context
from database.db import get_db
from database.models.project import Project
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.project_router import router as project_router
from auth.workspace_router import router as workspace_router
from auth.router import router as auth_router
from auth.account_router import router as account_router
from database.init_db import init_db
from dashboard.config import settings
from dashboard.logging_config import configure_logging
from dashboard.security import SecurityHeadersMiddleware
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

configure_logging()

init_db()

app = FastAPI(
    title="Cloud Economics Intelligence Platform",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

@app.get("/", include_in_schema=False)
def api_root():
    return {"service": settings.app_name, "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "causal-cost-dashboard"
    }


def _active_project(context, db):
    return db.scalar(select(Project).where(Project.organization_id == context["organization_id"]).order_by(Project.created_at).limit(1))


@app.get("/api/causal-chain")
def causal_chain(context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    project = _active_project(context, db)
    return project_causal(project.id, context, db)["chain"] if project else {}


@app.get("/api/causal-candidates")
def causal_candidates(context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    project = _active_project(context, db)
    return project_causal(project.id, context, db)["candidates"] if project else []


@app.get("/api/anomalies")
def anomalies(context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    project = _active_project(context, db)
    return project_anomalies(project.id, context, db) if project else {"anomalies": []}


@app.get("/api/cost")
def cost(context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    project = _active_project(context, db)
    return project_cost(project.id, context, db) if project else {"source": "Local Demo Data", "services": []}


app.include_router(auth_router)
app.include_router(account_router)
app.include_router(project_router)
app.include_router(workspace_router)
app.include_router(cloud_router)
app.include_router(connection_router)
app.include_router(intelligence_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8081
    )
