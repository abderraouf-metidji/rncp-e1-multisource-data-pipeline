from datetime import datetime
from decimal import Decimal
from pydantic import Field
from src.api.schemas.common import ORMModel


class IndicatorCreate(ORMModel):
    country_id: int = Field(gt=0)
    indicator_year: int = Field(ge=1900, le=2100)
    population: int | None = Field(default=None, ge=0)
    area_km2: Decimal | None = Field(default=None, gt=0)
    gdp_usd: Decimal | None = Field(default=None, ge=0)
    density_per_km2: Decimal | None = Field(default=None, ge=0)
    gdp_per_capita_usd: Decimal | None = Field(default=None, ge=0)


class IndicatorUpdate(IndicatorCreate):
    pass


class IndicatorRead(IndicatorCreate):
    country_indicator_id: int
    loaded_at: datetime
