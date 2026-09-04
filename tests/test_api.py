import sys
import os
import pytest
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from app.main import app
from app.database import get_db
from app.models import SessionModel, ArtifactModel
from app.services.sanitizer import sanitize_html

dummy_session = SessionModel(id=uuid4())
malicious_payload = "<div><h1>Empowered Teams</h1><script>alert('XSS')</script><img src='x' onerror='alert(1)'><a href='javascript:alert(2)'>click</a></div>"
clean_payload = sanitize_html(malicious_payload)

dummy_artifact = ArtifactModel(
    id=uuid4(),
    session_id=dummy_session.id,
    type="html",
    content=clean_payload,
    sanitized=True
)

class MockQueryResult:
    def __init__(self, target_obj=None):
        self.target_obj = target_obj or dummy_session
    def scalar_one_or_none(self):
        return self.target_obj
    def scalar(self):
        return 1
    def scalars(self):
        return self
    def all(self):
        return []

async def override_get_db():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    
    async def mock_execute(stmt, *args, **kwargs):
        stmt_str = str(stmt).lower()
        if "artifacts" in stmt_str:
            return MockQueryResult(dummy_artifact)
        return MockQueryResult(dummy_session)

    mock_session.execute = AsyncMock(side_effect=mock_execute)
    mock_session.commit = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    yield mock_session

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_api_404_error_envelope():
    response = client.get("/nonexistent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"

def test_api_config_endpoint():
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "active_provider" in data
    assert "embedding_model" in data
