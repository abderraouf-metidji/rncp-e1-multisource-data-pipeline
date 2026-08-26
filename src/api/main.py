from __future__ import annotations

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.config import settings
from src.api.database import get_db
from src.api.routers.resources import audits_router, countries_router, indicators_router, regions_router, subregions_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API REST sécurisée exposant le référentiel pays et les indicateurs du schéma C4.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.get("/health", tags=["Technique"])
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "reachable"}


app.include_router(regions_router)
app.include_router(subregions_router)
app.include_router(countries_router)
app.include_router(indicators_router)
app.include_router(audits_router)
