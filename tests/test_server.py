"""Tests for Flask backend middleware and bridge behavior."""

import base64
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture()
def server_module(monkeypatch):
    """Reload server module with deterministic env configuration."""
    monkeypatch.setenv("BRIDGE_SECRET_916", "bridge-test-secret")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    if "server" in sys.modules:
        module = importlib.reload(sys.modules["server"])
    else:
        module = importlib.import_module("server")
    return module


def test_health_does_not_require_secret(server_module):
    client = server_module.app.test_client()
    response = client.get("/health")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["bridge_secret_protected"] is True


def test_translate_requires_secret(server_module):
    client = server_module.app.test_client()
    response = client.post("/api/translate", json={"message": "hello"})
    assert response.status_code == 401


def test_translate_with_secret(server_module):
    client = server_module.app.test_client()
    response = client.post(
        "/api/translate",
        headers={"X-API-Key": "bridge-test-secret"},
        json={"message": "Turn on the lights", "format": "ai"},
    )
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["format"] == "ai"
    assert "TASK_INTENT: COMMAND" in payload["translated"]
    assert payload["surface_input"] == "Turn on the lights"
    assert "substrate_truth" in payload
    assert "resonance_score" in payload


def test_bridge_requires_secret(server_module):
    client = server_module.app.test_client()
    response = client.post("/api/bridge", json={"text": "hello"})
    assert response.status_code == 401


def test_bridge_normalizes_base64(server_module):
    client = server_module.app.test_client()
    encoded = base64.b64encode(b"turn on the lights").decode("ascii")
    response = client.post(
        "/api/bridge",
        headers={"X-API-Key": "bridge-test-secret"},
        json={"text": encoded, "direction": "human_to_ai"},
    )
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["normalized_input"] == "turn on the lights"
    assert isinstance(payload["attempts"], list)
    assert payload["attempts"][0]["status"] == "ok"


def test_bridge_retry_cap(server_module):
    client = server_module.app.test_client()
    response = client.post(
        "/api/bridge",
        headers={"X-API-Key": "bridge-test-secret"},
        json={"text": "echo", "direction": "ai_to_human", "max_retries": 9},
    )
    payload = response.get_json()
    assert response.status_code == 200
    assert len(payload["attempts"]) <= 3
    assert payload["final_status"] in {"ok", "retry_exhausted"}


def test_chat_returns_503_without_groq_key(server_module):
    client = server_module.app.test_client()
    response = client.post(
        "/api/chat",
        headers={"X-API-Key": "bridge-test-secret"},
        json={"message": "hello"},
    )
    assert response.status_code == 503
