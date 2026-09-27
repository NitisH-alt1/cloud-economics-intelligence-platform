from fastapi import APIRouter, Depends

from auth.dependencies import get_current_context


router = APIRouter(
    prefix="/api/account",
    tags=["Account"],
)


@router.get("/me")
def get_me(
    context: dict = Depends(get_current_context),
):
    user = context["user"]

    return {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "organization_id": context["organization_id"],
        "role": context["role"],
    }
