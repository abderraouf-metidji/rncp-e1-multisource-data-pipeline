from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.models import Country, CountryIndicator, DataLoadAudit, Region, Subregion
from src.api.routers.crud_factory import build_crud_router
from src.api.schemas.audit import AuditRead
from src.api.schemas.country import CountryCreate, CountryRead, CountryUpdate
from src.api.schemas.indicator import IndicatorCreate, IndicatorRead, IndicatorUpdate
from src.api.schemas.region import RegionCreate, RegionRead, RegionUpdate
from src.api.schemas.subregion import SubregionCreate, SubregionRead, SubregionUpdate
from src.api.security import require_auth

regions_router = build_crud_router(prefix="/regions", tag="Regions", model=Region, create_schema=RegionCreate, update_schema=RegionUpdate, read_schema=RegionRead, id_attribute="region_id", search_attribute="region_name")
subregions_router = build_crud_router(prefix="/subregions", tag="Sous-régions", model=Subregion, create_schema=SubregionCreate, update_schema=SubregionUpdate, read_schema=SubregionRead, id_attribute="subregion_id", search_attribute="subregion_name")
countries_router = build_crud_router(prefix="/countries", tag="Pays", model=Country, create_schema=CountryCreate, update_schema=CountryUpdate, read_schema=CountryRead, id_attribute="country_id", search_attribute="country_name")
indicators_router = build_crud_router(prefix="/indicators", tag="Indicateurs", model=CountryIndicator, create_schema=IndicatorCreate, update_schema=IndicatorUpdate, read_schema=IndicatorRead, id_attribute="country_indicator_id")

audits_router = APIRouter(prefix="/audits", tags=["Audits"], dependencies=[Depends(require_auth)])


@audits_router.get("/", response_model=list[AuditRead])
def list_audits(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    statement = select(DataLoadAudit).order_by(DataLoadAudit.started_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(statement).all())


@audits_router.get("/{load_id}", response_model=AuditRead)
def get_audit(load_id: str, db: Session = Depends(get_db)):
    item = db.get(DataLoadAudit, load_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Audit introuvable")
    return item
