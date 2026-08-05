from pydantic import BaseModel, ConfigDict


class OIDDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    oid: str
    name: str | None = None
    short_name: str | None = None
    category: str | None = None
    description: str | None = None
    enabled: bool = True
