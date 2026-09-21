from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from src.api.config import settings

security = HTTPBasic()


def require_auth(credentials: Annotated[HTTPBasicCredentials, Depends(security)]) -> str:
    if not settings.auth_is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentification API non configurée",
        )
    username_ok = secrets.compare_digest(credentials.username.encode(), settings.api_username.encode())
    password_ok = secrets.compare_digest(credentials.password.encode(), settings.api_password.encode())
    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
