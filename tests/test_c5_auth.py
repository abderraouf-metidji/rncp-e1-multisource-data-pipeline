from fastapi.testclient import TestClient
from src.api.config import settings
from src.api.database import get_db
from src.api.main import app


class EmptyScalars:
    def all(self):
        return []


class FakeDB:
    def execute(self, statement): return None
    def scalars(self, statement): return EmptyScalars()


def override_db():
    yield FakeDB()


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


def test_valid_basic_auth_allows_access(monkeypatch):
    monkeypatch.setattr(settings, "api_username", "test-user")
    monkeypatch.setattr(settings, "api_password", "a-secure-test-password")
    response = client.get("/countries/", auth=(settings.api_username, settings.api_password))
    assert response.status_code == 200
    assert response.json() == []


def test_invalid_basic_auth_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "api_username", "test-user")
    monkeypatch.setattr(settings, "api_password", "a-secure-test-password")
    response = client.get("/countries/", auth=("bad", "credentials"))
    assert response.status_code == 401


def test_unconfigured_authentication_fails_closed(monkeypatch):
    monkeypatch.setattr(settings, "api_username", "")
    monkeypatch.setattr(settings, "api_password", "")
    response = client.get("/countries/", auth=("rncp", "change-me"))
    assert response.status_code == 503
    assert response.json()["detail"] == "Authentification API non configurée"
