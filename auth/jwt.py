from datetime import datetime, timedelta, timezone
from jose import jwt

from auth.config import (
    JWT_ALGORITHM as ALGORITHM,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET_KEY as SECRET_KEY,
)


def create_access_token(
    user_id: str,
    organization_id: str,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_id,
        "organization_id": organization_id,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )
