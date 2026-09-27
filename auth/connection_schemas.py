from pydantic import BaseModel, Field

SUPPORTED_PROVIDERS = {"aws", "azure", "gcp"}
SUPPORTED_AUTH_METHODS = {
    "aws_role",
    "azure_service_principal",
    "gcp_service_account",
}


class CloudConnectionCreate(BaseModel):
    cloud_account_id: str = Field(min_length=1, max_length=36)
    provider: str
    auth_method: str


class CloudConnectionResponse(BaseModel):
    id: str
    cloud_account_id: str
    provider: str
    auth_method: str
    status: str
