from fastapi import APIRouter, Depends

from auth.dependencies import get_current_context


router = APIRouter(
    prefix="/api/workspace",
    tags=["Workspace"],
)


@router.get("/summary")
def workspace_summary(
    context: dict = Depends(get_current_context),
):
    user = context["user"]

    return {
        "user": {
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
        },
        "organization": {
            "id": context["organization_id"],
            "role": context["role"],
        },
        "status": "active",
    }
