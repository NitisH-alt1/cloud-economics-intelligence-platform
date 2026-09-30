from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from auth.account_router import get_current_context
from auth.connection_schemas import (
    CloudConnectionCreate,
    CloudConnectionResponse,
    SUPPORTED_AUTH_METHODS,
    SUPPORTED_PROVIDERS,
)
from database.db import SessionLocal
from database.models.cloud_account import CloudAccount
from database.models.cloud_connection import CloudConnection

router = APIRouter(
    prefix="/api/cloud-connections",
    tags=["Cloud Connections"],
)


@router.get("", response_model=list[CloudConnectionResponse])
def list_connections(
    context: dict = Depends(get_current_context),
):
    organization_id = context["organization_id"]

    with SessionLocal() as db:
        rows = db.execute(
            select(CloudConnection).where(
                CloudConnection.organization_id == organization_id
            )
        ).scalars().all()

        return [
            CloudConnectionResponse(
                id=row.id,
                cloud_account_id=row.cloud_account_id,
                provider=row.provider,
                auth_method=row.auth_method,
                status=row.status,
            )
            for row in rows
        ]


@router.post("", response_model=CloudConnectionResponse)
def create_connection(
    payload: CloudConnectionCreate,
    context: dict = Depends(get_current_context),
):
    provider = payload.provider.lower().strip()
    auth_method = payload.auth_method.lower().strip()

    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported cloud provider.",
        )

    if auth_method not in SUPPORTED_AUTH_METHODS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported authentication method.",
        )

    with SessionLocal() as db:
        account = db.execute(
            select(CloudAccount).where(
                CloudAccount.id == payload.cloud_account_id,
                CloudAccount.organization_id == context["organization_id"],
            )
        ).scalar_one_or_none()

        if account is None:
            raise HTTPException(
                status_code=404,
                detail="Cloud account not found.",
            )

        if account.provider != provider:
            raise HTTPException(
                status_code=400,
                detail="Provider does not match cloud account.",
            )

        connection = CloudConnection(
            organization_id=context["organization_id"],
            cloud_account_id=account.id,
            provider=provider,
            auth_method=auth_method,
            status="configured",
        )

        db.add(connection)
        db.commit()
        db.refresh(connection)

        return CloudConnectionResponse(
            id=connection.id,
            cloud_account_id=connection.cloud_account_id,
            provider=connection.provider,
            auth_method=connection.auth_method,
            status=connection.status,
        )


@router.delete("/{connection_id}")
def delete_connection(
    connection_id: str,
    context: dict = Depends(get_current_context),
):
    with SessionLocal() as db:
        connection = db.execute(
            select(CloudConnection).where(
                CloudConnection.id == connection_id,
                CloudConnection.organization_id == context["organization_id"],
            )
        ).scalar_one_or_none()

        if connection is None:
            raise HTTPException(
                status_code=404,
                detail="Cloud connection not found.",
            )

        db.delete(connection)
        db.commit()

        return {"status": "deleted"}
