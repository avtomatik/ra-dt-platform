from pydantic import BaseModel, ConfigDict


class SnapshotModel(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)
