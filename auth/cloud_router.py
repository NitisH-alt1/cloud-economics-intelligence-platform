from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.cloud_schemas import (
    CloudAccountCreate,
    CloudAccountResponse,
    SUPPORTED_PROVIDERS,
)
from auth.dependencies import get_current_context
from database.db import get_db
from database.models.cloud_account import CloudAccount
from database.models.cloud_connection import CloudConnection
from database.models.cost_record import CostRecord
from database.models.project import project_cloud_accounts


router = APIRouter(
    prefix="/api/cloud-accounts",
    tags=["Cloud Accounts"],
)


@router.get("")
def list_cloud_accounts(
    context: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    organization_id = context["organization_id"]

    accounts = db.scalars(
        select(CloudAccount)
        .where(
            CloudAccount.organization_id == organization_id
        )
        .order_by(CloudAccount.created_at.desc())
    ).all()

    return [
        {
            "id": account.id,
            "provider": account.provider,
            "display_name": account.display_name,
            "external_account_id": account.external_account_id,
            "region": account.region,
            "auth_method": account.auth_method,
            "status": account.status,
        }
        for account in accounts
    ]


@router.post(
    "",
    response_model=CloudAccountResponse,
)
def create_cloud_account(
    request: CloudAccountCreate,
    context: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    organization_id = context["organization_id"]

    provider = request.provider.strip().lower()

    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail="Supported providers: aws, azure, gcp.",
        )

    display_name = request.display_name.strip()
    external_id = request.external_account_id.strip()

    existing = db.scalar(
        select(CloudAccount).where(
            CloudAccount.organization_id == organization_id,
            CloudAccount.provider == provider,
            CloudAccount.external_account_id == external_id,
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This cloud account is already registered.",
        )

    account = CloudAccount(
        organization_id=organization_id,
        provider=provider,
        display_name=display_name,
        external_account_id=external_id,
        region=request.region,
        auth_method="pending",
        status="pending",
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account


@router.delete("/{account_id}")
def delete_cloud_account(
    account_id: str,
    context: dict = Depends(get_current_context),
    db: Session = Depends(get_db),
):
    organization_id = context["organization_id"]

    account = db.scalar(
        select(CloudAccount).where(
            CloudAccount.id == account_id,
            CloudAccount.organization_id == organization_id,
        )
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Cloud account not found.",
        )

    affected_project_ids = db.scalars(
        select(project_cloud_accounts.c.project_id).where(
            project_cloud_accounts.c.cloud_account_id == account_id
        )
    ).all()
    if affected_project_ids:
        db.query(CostRecord).filter(
            CostRecord.organization_id == organization_id,
            CostRecord.project_id.in_(affected_project_ids),
            CostRecord.source == "local-demo",
        ).delete(synchronize_session=False)

    db.query(CloudConnection).filter(
        CloudConnection.organization_id == organization_id,
        CloudConnection.cloud_account_id == account_id,
    ).delete(synchronize_session=False)
    db.execute(
        project_cloud_accounts.delete().where(
            project_cloud_accounts.c.cloud_account_id == account_id
        )
    )
    db.delete(account)
    db.commit()

    return {
        "status": "deleted",
        "account_id": account_id,
    }
