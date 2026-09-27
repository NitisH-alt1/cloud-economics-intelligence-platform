from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from auth.jwt import decode_access_token
from database.db import get_db
from database.models import Membership, User


security = HTTPBearer()


def get_current_context(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):

    try:
        payload = decode_access_token(
            credentials.credentials
        )

        user_id = payload.get("sub")
        organization_id = payload.get("organization_id")

        if not user_id or not organization_id:
            raise ValueError()

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )

    user = db.get(User, user_id)

    membership = db.query(Membership).filter(
        Membership.user_id == user_id,
        Membership.organization_id == organization_id,
    ).first()

    if not user or not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization access denied.",
        )

    return {
        "user": user,
        "organization_id": organization_id,
        "role": membership.role,
    }
