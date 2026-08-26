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


def test_valid_basic_auth_allows_access():
    response = client.get("/countries/", auth=(settings.api_username, settings.api_password))
    assert response.status_code == 200
    assert response.json() == []


def test_invalid_basic_auth_is_rejected():
    response = client.get("/countries/", auth=("bad", "credentials"))
    assert response.status_code == 401
