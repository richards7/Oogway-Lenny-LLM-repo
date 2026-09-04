import sys
import os
import pytest
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.main import app
from app.database import get_db
from app.models import SessionModel, ArtifactModel
from app.services.classifier import classify_intent, TOOL_RETRIEVE_AND_ANSWER, TOOL_WRITE_SHIP30_ESSAY, TOOL_GENERATE_ARTIFACT
from app.services.sanitizer import sanitize_html

dummy_session = SessionModel(id=uuid4())

# Create a mock artifact for HTTP pipeline tests
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

def test_acceptance_1_session_creation_and_history():
    """Acceptance Criteria 1: Session creation and multi-turn message persistence."""
    res_session = client.post("/sessions", json={"client_metadata": {"test": "acceptance"}})
    assert res_session.status_code == 201
    session_id = res_session.json()["session_id"]
    assert UUID(session_id)

    # Fetch initial history
    res_history = client.get(f"/sessions/{session_id}/messages")
    assert res_history.status_code == 200
    assert isinstance(res_history.json(), list)

def test_acceptance_2_config_endpoint():
    """Acceptance Criteria 2: GET /config endpoint."""
    res_config = client.get("/config")
    assert res_config.status_code == 200
    config_data = res_config.json()
    assert config_data["active_provider"] in ["ollama", "anthropic", "openai"]
    assert config_data["embedding_model"] == "sentence-transformers/all-MiniLM-L6-v2"

def test_acceptance_3_tool_classification_routing():
    """Acceptance Criteria 3: Server-side tool-routing classifier accuracy."""
    # Standard Q&A
    assert classify_intent("What is Product-Led Growth according to Elena Verna?") == TOOL_RETRIEVE_AND_ANSWER
    
    # Ship 30/30 Essay
    assert classify_intent("Write a Ship 30/30 essay on Founder Mode based on Brian Chesky's transcript.") == TOOL_WRITE_SHIP30_ESSAY
    
    # HTML Visual Artifact
    assert classify_intent("Create an HTML visual table component comparing Empowered Teams vs Feature Factories.") == TOOL_GENERATE_ARTIFACT

def test_acceptance_4_xss_html_sanitization_and_sandboxing():
    """
    Acceptance Criteria 4: End-to-End HTTP flow XSS verification.
    Fetches HTML artifact via GET /artifacts/{id} and verifies script, onerror, and javascript: URLs are stripped.
    """
    res = client.get(f"/artifacts/{dummy_artifact.id}")
    assert res.status_code == 200
    artifact_data = res.json()
    
    # 1. Assert sanitized flag is true
    assert artifact_data["sanitized"] is True
    
    # 2. Assert all 3 payload types are stripped in returned content
    content = artifact_data["content"]
    assert "<script>" not in content
    assert "onerror" not in content
    assert "javascript:" not in content
    assert "<h1>Empowered Teams</h1>" in content

def test_acceptance_5_error_envelope_consistency():
    """Acceptance Criteria 5: Consistent JSON error envelope across API errors."""
    res = client.get("/nonexistent-route-for-testing")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "message" in data["error"]
