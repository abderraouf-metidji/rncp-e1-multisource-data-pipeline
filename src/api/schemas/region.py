from datetime import datetime
from pydantic import Field
from src.api.schemas.common import ORMModel


class RegionCreate(ORMModel):
    region_name: str = Field(min_length=1, max_length=100)


class RegionUpdate(ORMModel):
    region_name: str = Field(min_length=1, max_length=100)


class RegionRead(RegionCreate):
    region_id: int
    created_at: datetime
