from pydantic import BaseModel, Field


SUPPORTED_PROVIDERS = {
    "aws",
    "azure",
    "gcp",
}


class CloudAccountCreate(BaseModel):
    provider: str
    display_name: str = Field(min_length=2, max_length=120)
    external_account_id: str = Field(
        min_length=2,
        max_length=200,
    )
    region: str | None = Field(
        default=None,
        max_length=100,
    )


class CloudAccountResponse(BaseModel):
    id: str
    provider: str
    display_name: str
    external_account_id: str
    region: str | None
    auth_method: str
    status: str
