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

    return slug or "project"


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
