from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "RNCP E1 - Countries API"
    app_version: str = "1.0.0"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://rncp:rncp@localhost:5432/countries",
    )
    api_username: str = os.getenv("API_USERNAME", "rncp")
    api_password: str = os.getenv("API_PASSWORD", "change-me")


settings = Settings()
