import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.dependencies import get_current_context
from auth.project_schemas import (
    ProjectCreate,
    ProjectResponse,
)
from database.db import get_db
from database.models import Project
from database.models.cloud_account import CloudAccount
from database.models.cost_record import CostRecord
from database.models.project import project_cloud_accounts


router = APIRouter(
    prefix="/api/projects",
    tags=["Projects"],
)


def make_slug(name: str) -> str:
    slug = re.sub(
        r"[^a-zA-Z0-9]+",
        "-",
        name.strip().lower(),
    ).strip("-")

    return (slug or "project")[:100]


@router.get("")
def list_projects(
    context: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    organization_id = context["organization_id"]

    projects = db.scalars(
        select(Project)
        .where(
            Project.organization_id == organization_id
        )
        .order_by(Project.created_at.desc())
    ).all()

    return [
        {
            "id": project.id,
            "name": project.name,
            "slug": project.slug,
            "organization_id": project.organization_id,
            "description": project.description,
        }
        for project in projects
    ]


@router.post(
    "",
    response_model=ProjectResponse,
)
def create_project(
    request: ProjectCreate,
    context: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    organization_id = context["organization_id"]

    name = request.name.strip()

    if len(name) < 2:
        raise HTTPException(
            status_code=400,
            detail="Project name is too short.",
        )

    description = request.description

    if description is not None:
        description = description.strip()
        if not description:
            description = None
        elif len(description) > 500:
            raise HTTPException(
                status_code=400,
                detail="Project description must be 500 characters or fewer.",
            )

    slug = make_slug(name)

    existing = db.scalar(
        select(Project).where(
            Project.organization_id == organization_id,
            Project.slug == slug,
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="A project with this name already exists.",
        )

    project = Project(
        organization_id=organization_id,
        name=name,
        slug=slug,
        description=description,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        slug=project.slug,
        organization_id=project.organization_id,
        description=project.description,
    )


@router.get("/{project_id}")
def get_project(project_id: str, context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    project = db.scalar(select(Project).where(Project.id == project_id, Project.organization_id == context["organization_id"]))
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"id": project.id, "name": project.name, "slug": project.slug, "description": project.description, "organization_id": project.organization_id}


@router.put("/{project_id}")
def update_project(project_id: str, request: ProjectCreate, context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    project = db.scalar(select(Project).where(Project.id == project_id, Project.organization_id == context["organization_id"]))
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    name = request.name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Project name is too short.")
    slug = make_slug(name)
    duplicate = db.scalar(select(Project).where(Project.organization_id == context["organization_id"], Project.slug == slug, Project.id != project_id))
    if duplicate:
        raise HTTPException(status_code=409, detail="A project with this name already exists.")
    project.name, project.slug = name, slug
    project.description = request.description.strip() or None if request.description else None
    db.commit()
    return {"id": project.id, "name": project.name, "slug": project.slug, "description": project.description, "organization_id": project.organization_id}


@router.delete("/{project_id}")
def delete_project(project_id: str, context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    project = db.scalar(select(Project).where(Project.id == project_id, Project.organization_id == context["organization_id"]))
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    db.query(CostRecord).filter(
        CostRecord.organization_id == context["organization_id"],
        CostRecord.project_id == project_id,
    ).delete(synchronize_session=False)
    db.execute(project_cloud_accounts.delete().where(project_cloud_accounts.c.project_id == project_id))
    db.delete(project)
    db.commit()
    return {"status": "deleted", "project_id": project_id}


@router.get("/{project_id}/cloud-accounts")
def get_project_cloud_accounts(project_id: str, context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    project = db.scalar(select(Project).where(Project.id == project_id, Project.organization_id == context["organization_id"]))
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return db.execute(select(CloudAccount).join(project_cloud_accounts, CloudAccount.id == project_cloud_accounts.c.cloud_account_id).where(project_cloud_accounts.c.project_id == project_id, CloudAccount.organization_id == context["organization_id"])).scalars().all()


@router.put("/{project_id}/cloud-accounts/{account_id}")
def associate_cloud_account(project_id: str, account_id: str, context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    organization_id = context["organization_id"]
    project = db.scalar(select(Project).where(Project.id == project_id, Project.organization_id == organization_id))
    account = db.scalar(select(CloudAccount).where(CloudAccount.id == account_id, CloudAccount.organization_id == organization_id))
    if project is None or account is None:
        raise HTTPException(status_code=404, detail="Project or cloud account not found.")
    linked = db.execute(select(project_cloud_accounts).where(project_cloud_accounts.c.project_id == project_id, project_cloud_accounts.c.cloud_account_id == account_id)).first()
    if not linked:
        db.execute(project_cloud_accounts.insert().values(project_id=project_id, cloud_account_id=account_id))
        db.query(CostRecord).filter(
            CostRecord.organization_id == organization_id,
            CostRecord.project_id == project_id,
            CostRecord.source == "local-demo",
        ).delete(synchronize_session=False)
    db.commit()
    return {"status": "associated", "project_id": project_id, "cloud_account_id": account_id}


@router.delete("/{project_id}/cloud-accounts/{account_id}")
def disassociate_cloud_account(project_id: str, account_id: str, context: dict = Depends(get_current_context), db: Session = Depends(get_db)):
    organization_id = context["organization_id"]
    project = db.scalar(select(Project).where(Project.id == project_id, Project.organization_id == organization_id))
    account = db.scalar(select(CloudAccount).where(CloudAccount.id == account_id, CloudAccount.organization_id == organization_id))
    if project is None or account is None:
        raise HTTPException(status_code=404, detail="Project or cloud account not found.")
    db.execute(project_cloud_accounts.delete().where(project_cloud_accounts.c.project_id == project_id, project_cloud_accounts.c.cloud_account_id == account_id))
    db.query(CostRecord).filter(
        CostRecord.organization_id == organization_id,
        CostRecord.project_id == project_id,
        CostRecord.source == "local-demo",
    ).delete(synchronize_session=False)
    db.commit()
    return {"status": "disassociated", "project_id": project_id, "cloud_account_id": account_id}
