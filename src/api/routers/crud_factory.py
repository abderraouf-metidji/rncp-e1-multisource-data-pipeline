from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Type

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.security import require_auth


def build_crud_router(
    *, prefix: str, tag: str, model: Type[Any], create_schema: Type[BaseModel],
    update_schema: Type[BaseModel], read_schema: Type[BaseModel],
    id_attribute: str, search_attribute: str | None = None,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag], dependencies=[Depends(require_auth)])
    id_column = getattr(model, id_attribute)

    def list_items(
        limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
        search: str | None = Query(None, min_length=1, max_length=150),
        db: Session = Depends(get_db),
    ) -> list[Any]:
        statement = select(model)
        if search and search_attribute:
            statement = statement.where(getattr(model, search_attribute).ilike(f"%{search}%"))
        return list(db.scalars(statement.order_by(id_column).offset(offset).limit(limit)).all())

    def get_item(item_id: int, db: Session = Depends(get_db)) -> Any:
        item = db.get(model, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"{tag} introuvable")
        return item

    def create_item(payload: Any, db: Session = Depends(get_db)) -> Any:
        values = payload.model_dump()
        if "created_at" in model.__table__.columns and "created_at" not in values:
            values["created_at"] = datetime.now(timezone.utc)
        if "loaded_at" in model.__table__.columns and "loaded_at" not in values:
            values["loaded_at"] = datetime.now(timezone.utc)
        item = model(**values)
        db.add(item)
        try:
            db.commit(); db.refresh(item); return item
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="Conflit d'intégrité") from exc

    def update_item(item_id: int, payload: Any, db: Session = Depends(get_db)) -> Any:
        item = db.get(model, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"{tag} introuvable")
        for key, value in payload.model_dump().items():
            setattr(item, key, value)
        if hasattr(item, "loaded_at"):
            item.loaded_at = datetime.now(timezone.utc)
        try:
            db.commit(); db.refresh(item); return item
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="Conflit d'intégrité") from exc

    def delete_item(item_id: int, db: Session = Depends(get_db)) -> Response:
        item = db.get(model, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"{tag} introuvable")
        db.delete(item)
        try:
            db.commit(); return Response(status_code=status.HTTP_204_NO_CONTENT)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="Suppression impossible: ressource référencée") from exc

    create_item.__annotations__["payload"] = create_schema
    create_item.__annotations__["return"] = Any
    update_item.__annotations__["payload"] = update_schema
    update_item.__annotations__["return"] = Any

    router.add_api_route("/", list_items, methods=["GET"], response_model=list[read_schema])
    router.add_api_route("/{item_id}", get_item, methods=["GET"], response_model=read_schema)
    router.add_api_route("/", create_item, methods=["POST"], response_model=read_schema, status_code=201)
    router.add_api_route("/{item_id}", update_item, methods=["PUT"], response_model=read_schema)
    router.add_api_route("/{item_id}", delete_item, methods=["DELETE"], status_code=204)
    return router
