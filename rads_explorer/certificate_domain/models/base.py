from pydantic import BaseModel, ConfigDict


class DomainModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, validate_assignment=True
    )
