from datetime import datetime, timezone
from pydantic import Field, field_validator
from src.api.schemas.common import ORMModel


class CountryCreate(ORMModel):
    region_id: int | None = Field(default=None, gt=0)
    subregion_id: int | None = Field(default=None, gt=0)
    iso2: str = Field(min_length=2, max_length=2)
    iso3: str = Field(min_length=3, max_length=3)
    country_name: str = Field(min_length=1, max_length=150)
    official_name: str | None = Field(default=None, max_length=200)
    capital: str | None = Field(default=None, max_length=150)
    currencies: str | None = None
    languages: str | None = None
    source_count: int = Field(default=1, ge=1)
    sources: str = Field(min_length=1)
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("iso2", "iso3")
    @classmethod
    def uppercase_iso(cls, value: str) -> str:
        if not value.isalpha():
            raise ValueError("Le code ISO doit contenir uniquement des lettres")
        return value.upper()


class CountryUpdate(CountryCreate):
    pass


class CountryRead(CountryCreate):
    country_id: int
    loaded_at: datetime
