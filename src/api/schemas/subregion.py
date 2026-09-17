from datetime import datetime
from pydantic import Field
from src.api.schemas.common import ORMModel


class SubregionCreate(ORMModel):
    region_id: int = Field(gt=0)
    subregion_name: str = Field(min_length=1, max_length=100)


class SubregionUpdate(SubregionCreate):
    pass


class SubregionRead(SubregionCreate):
    subregion_id: int
    created_at: datetime
