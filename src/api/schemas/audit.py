import uuid
from datetime import datetime
from src.api.schemas.common import ORMModel


class AuditRead(ORMModel):
    load_id: uuid.UUID
    source_file: str
    source_sha256: str
    started_at: datetime
    completed_at: datetime | None
    status: str
    rows_read: int
    countries_inserted: int
    countries_updated: int
    indicators_upserted: int
    error_message: str | None
