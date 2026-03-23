"""Tests for Flask backend middleware and API behavior."""

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture()
def server_module(monkeypatch):
    """Reload server module with deterministic env configuration."""
    monkeypatch.setenv("BACKEND_API_KEY", "test-key")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    if "server" in sys.modules:
        module = importlib.reload(sys.modules["server"])
    else:
        module = importlib.import_module("server")
    return module


def test_health_does_not_require_api_key(server_module):
    client = server_module.app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["status"] == "ok"
    assert payload["api_key_protected"] is True


def test_translate_requires_api_key(server_module):
    client = server_module.app.test_client()
    resp = client.post("/api/translate", json={"message": "hello"})
    assert resp.status_code == 401


def test_translate_with_api_key(server_module):
    client = server_module.app.test_client()
    resp = client.post(
        "/api/translate",
        headers={"X-API-Key": "test-key"},
        json={"message": "Turn on the lights", "format": "ai"},
    )
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["format"] == "ai"
    assert "TASK_INTENT: COMMAND" in payload["translated"]


def test_chat_returns_503_without_groq_key(server_module):
    client = server_module.app.test_client()
    resp = client.post(
        "/api/chat",
        headers={"X-API-Key": "test-key"},
        json={"message": "hello"},
    )
    assert resp.status_code == 503

