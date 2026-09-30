from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=500)


class ProjectResponse(BaseModel):
    id: str
    name: str
    slug: str
    organization_id: str
    description: str | None = None
