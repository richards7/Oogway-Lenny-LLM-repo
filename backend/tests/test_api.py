import httpx
import pytest
import uuid
import json

BASE_URL = "http://localhost:5001"

def test_health():
    """Test the health check endpoint returns 200 OK and correct JSON structure."""
    response = httpx.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert "llm_provider" in data

def test_config():
    """Test the config endpoint returns 200 OK and provider list."""
    response = httpx.get(f"{BASE_URL}/config")
    assert response.status_code == 200
    data = response.json()
    assert "active_provider" in data
    assert "providers" in data
    assert len(data["providers"]) > 0

def test_get_sessions():
    """Test the sessions endpoint returns a list."""
    response = httpx.get(f"{BASE_URL}/sessions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_chat_interaction():
    """Test the chat endpoint by sending a query and validating the SSE response."""
    # 1. Create a session first
    session_response = httpx.post(f"{BASE_URL}/sessions", json={})
    assert session_response.status_code == 201
    session_id = session_response.json()["session_id"]
    
    # 2. Send the message payload
    payload = {
        "content": "What is Founder Mode?"
    }
    
    # The endpoint returns a standard JSON MessageResponse, not an SSE stream.
    response = httpx.post(f"{BASE_URL}/sessions/{session_id}/messages", json=payload, timeout=120.0)
    assert response.status_code == 200
    
    data = response.json()
    assert "content" in data
    assert "role" in data
    assert data["role"] == "assistant"
    
    full_response = data["content"]
    assert len(full_response) > 50
    assert "Founder" in full_response or "Chesky" in full_response or "mode" in full_response.lower()
