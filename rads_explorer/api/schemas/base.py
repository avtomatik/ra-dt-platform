from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True, extra="ignore", from_attributes=True
    )
