from fastapi.testclient import TestClient

from src.api.database import get_db
from src.api.main import app


class EmptyScalars:
    def all(self): return []

class FakeDB:
    def execute(self, statement): return None
    def scalars(self, statement): return EmptyScalars()


def override_db():
    yield FakeDB()


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


def test_health_is_public_and_works():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_resources_require_authentication():
    for path in ["/regions/", "/subregions/", "/countries/", "/indicators/", "/audits/"]:
        response = client.get(path)
        assert response.status_code == 401


def test_openapi_exposes_crud_routes():
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    for resource in ["regions", "subregions", "countries", "indicators"]:
        assert f"/{resource}/" in paths
        assert f"/{resource}/{{item_id}}" in paths
        assert {"get", "post"}.issubset(paths[f"/{resource}/"].keys())
        assert {"get", "put", "delete"}.issubset(paths[f"/{resource}/{{item_id}}"].keys())
