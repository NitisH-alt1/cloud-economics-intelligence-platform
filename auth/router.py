from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.db import get_db
from database.models.user import User
from database.models.organization import Organization
from database.models.membership import Membership

from auth.jwt import create_access_token
from auth.passwords import hash_password, verify_password
from auth.schemas import SignupRequest, LoginRequest, AuthResponse

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post(
    "/signup",
    response_model=AuthResponse,
)
def signup(
    request: SignupRequest,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    organization = Organization(
        name=request.organization_name,
    )

    db.add(organization)
    db.flush()

    user = User(
        email=request.email,
        full_name=request.full_name,
        password_hash=hash_password(request.password),
    )

    db.add(user)
    db.flush()

    membership = Membership(
        user_id=user.id,
        organization_id=organization.id,
        role="owner",
    )

    db.add(membership)
    db.commit()

    token = create_access_token(
        user_id=user.id,
        organization_id=organization.id,
    )

    return AuthResponse(
        access_token=token,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    membership = (
        db.query(Membership)
        .filter(Membership.user_id == user.id)
        .first()
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no organization membership.",
        )

    token = create_access_token(
        user_id=user.id,
        organization_id=membership.organization_id,
    )

    return AuthResponse(
        access_token=token,
    )
