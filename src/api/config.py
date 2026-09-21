from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


@dataclass
class Settings:
    app_name: str = "RNCP E1 - Countries API"
    app_version: str = "1.0.0"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://rncp:rncp@localhost:5432/countries",
    )
    api_username: str = os.getenv("API_USERNAME", "").strip()
    api_password: str = os.getenv("API_PASSWORD", "").strip()

    def auth_is_configured(self) -> bool:
        placeholders = {"change-me", "replace-with-a-long-random-password"}
        return bool(
            self.api_username
            and len(self.api_password) >= 12
            and self.api_password not in placeholders
        )


settings = Settings()
