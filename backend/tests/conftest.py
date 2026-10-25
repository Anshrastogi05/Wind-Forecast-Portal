import pytest


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from windportal.main import app
    return TestClient(app)
