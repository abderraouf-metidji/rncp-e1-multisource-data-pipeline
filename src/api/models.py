from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.api.database import Base


class Region(Base):
    __tablename__ = "region"
    region_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    region_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    subregions: Mapped[list["Subregion"]] = relationship(back_populates="region")
    countries: Mapped[list["Country"]] = relationship(back_populates="region")


class Subregion(Base):
    __tablename__ = "subregion"
    __table_args__ = (UniqueConstraint("region_id", "subregion_name", name="uq_subregion_region_name"),)
    subregion_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    region_id: Mapped[int] = mapped_column(ForeignKey("region.region_id", ondelete="RESTRICT"), nullable=False)
    subregion_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    region: Mapped[Region] = relationship(back_populates="subregions")
    countries: Mapped[list["Country"]] = relationship(back_populates="subregion")


class Country(Base):
    __tablename__ = "country"
    __table_args__ = (
        CheckConstraint("source_count >= 1", name="ck_country_source_count"),
    )
    country_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    region_id: Mapped[int | None] = mapped_column(ForeignKey("region.region_id", ondelete="SET NULL"))
    subregion_id: Mapped[int | None] = mapped_column(ForeignKey("subregion.subregion_id", ondelete="SET NULL"))
    iso2: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    iso3: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    country_name: Mapped[str] = mapped_column(String(150), nullable=False)
    official_name: Mapped[str | None] = mapped_column(String(200))
    capital: Mapped[str | None] = mapped_column(String(150))
    currencies: Mapped[str | None] = mapped_column(Text)
    languages: Mapped[str | None] = mapped_column(Text)
    source_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    sources: Mapped[str] = mapped_column(Text, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    loaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    region: Mapped[Region | None] = relationship(back_populates="countries")
    subregion: Mapped[Subregion | None] = relationship(back_populates="countries")
    indicators: Mapped[list["CountryIndicator"]] = relationship(back_populates="country", cascade="all, delete-orphan")


class CountryIndicator(Base):
    __tablename__ = "country_indicator"
    __table_args__ = (UniqueConstraint("country_id", "indicator_year", name="uq_country_indicator_year"),)
    country_indicator_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("country.country_id", ondelete="CASCADE"), nullable=False)
    indicator_year: Mapped[int] = mapped_column(Integer, nullable=False)
    population: Mapped[int | None] = mapped_column(BigInteger)
    area_km2: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    gdp_usd: Mapped[Decimal | None] = mapped_column(Numeric(22, 2))
    density_per_km2: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    gdp_per_capita_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    loaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    country: Mapped[Country] = relationship(back_populates="indicators")


class DataLoadAudit(Base):
    __tablename__ = "data_load_audit"
    load_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    source_file: Mapped[str] = mapped_column(String(500), nullable=False)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    rows_read: Mapped[int] = mapped_column(Integer, nullable=False)
    countries_inserted: Mapped[int] = mapped_column(Integer, nullable=False)
    countries_updated: Mapped[int] = mapped_column(Integer, nullable=False)
    indicators_upserted: Mapped[int] = mapped_column(Integer, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
