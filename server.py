"""Flask backend server for chat + symbolic translation.

All communication with the Groq API happens server-side.  The Groq API key
is **never** sent to the client; it is read exclusively from the
``GROQ_API_KEY`` environment variable (or a local ``.env`` file).

Usage
-----
1. Copy ``.env.example`` to ``.env`` and fill in your key::

       cp .env.example .env
       # then edit .env and add your GROQ_API_KEY

2. Start the server::

       python server.py

3. POST to the endpoint::

       curl -X POST http://localhost:5000/api/chat \\
            -H 'Content-Type: application/json' \\
            -d '{"message": "What is the capital of France?", "model": "llama3-8b-8192"}'

Environment variables
---------------------
GROQ_API_KEY  (required)
    Your Groq API key.  Never hardcode this value.
GROQ_MODEL    (optional, default: llama3-8b-8192)
    Default Groq model to use when the request does not specify one.
FLASK_DEBUG   (optional)
    Set to ``1`` to enable Flask debug mode (development only).
PORT          (optional)
    Port to bind to. Render injects this automatically for web services.
"""

from __future__ import annotations

import hmac
import os
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from src.translator import HumanToAITranslator
from werkzeug.exceptions import HTTPException

# Load variables from a local .env file (ignored by git) if present.
# Variables already set in the environment take precedence.
load_dotenv()

app = Flask(__name__)
_translator = HumanToAITranslator()

# ---------------------------------------------------------------------------
# Groq client — initialised once at startup
# ---------------------------------------------------------------------------

_GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
_groq_client = None
_groq_init_error = ""

if _GROQ_API_KEY:
    try:
        from groq import Groq  # type: ignore[import-untyped]
    except ImportError:
        _groq_init_error = (
            "The 'groq' package is not installed. Run: pip install groq"
        )
    else:
        _groq_client = Groq(api_key=_GROQ_API_KEY)
else:
    _groq_init_error = (
        "GROQ_API_KEY environment variable is not set. "
        "Copy .env.example to .env and add your key."
    )

_DEFAULT_MODEL = os.environ.get("GROQ_MODEL", "llama3-8b-8192")
_BACKEND_API_KEY = os.environ.get("BACKEND_API_KEY", "").strip()

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


def _extract_api_key() -> str:
    """Extract API key from request headers."""
    header_key = request.headers.get("X-API-Key", "").strip()
    if header_key:
        return header_key

    auth = request.headers.get("Authorization", "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return auth


@app.before_request
def require_api_key():
    """Protect API endpoints with a shared backend API key."""
    if request.path == "/health" or not request.path.startswith("/api/"):
        return None

    if not _BACKEND_API_KEY:
        return jsonify(
            {"error": "Server misconfiguration: BACKEND_API_KEY is not set."}
        ), 503

    provided_key = _extract_api_key()
    if not provided_key or not hmac.compare_digest(provided_key, _BACKEND_API_KEY):
        return jsonify({"error": "Unauthorized"}), 401
    return None


@app.errorhandler(Exception)
def handle_unexpected_error(exc: Exception):
    """Convert uncaught exceptions to stable JSON responses."""
    if isinstance(exc, HTTPException):
        return jsonify({"error": exc.description}), exc.code

    app.logger.exception("Unhandled server exception: %s", exc)
    return jsonify({"error": "Internal server error"}), 500


@app.route("/api/translate", methods=["POST"])
def translate() -> tuple:
    """Translate human text into symbolic or AI-oriented language."""
    data = request.get_json(silent=True)
    if not data or not data.get("message", "").strip():
        return jsonify({"error": "Request body must include a non-empty 'message' field."}), 400

    message: str = data["message"].strip()
    fmt: str = str(data.get("format", "ai")).lower()
    if fmt not in {"symbolic", "dict", "json", "ai"}:
        return jsonify({"error": "Invalid format. Use symbolic, dict, json, or ai."}), 400

    expr = _translator.translate(message)
    formatted: Any
    if fmt == "symbolic":
        formatted = str(expr)
    elif fmt == "dict":
        formatted = expr.to_dict()
    elif fmt == "json":
        formatted = expr.to_json()
    else:
        formatted = expr.to_ai_language()

    return jsonify(
        {
            "input": message,
            "format": fmt,
            "translated": formatted,
            "structured": expr.to_dict(),
        }
    ), 200


@app.route("/api/chat", methods=["POST"])
def chat() -> tuple:
    """Accept a user message and return the Groq model's reply.

    Request body (JSON)
    -------------------
    message : str  (required)
        The user's message.
    model : str  (optional)
        Groq model name to use for this request.
        Defaults to the ``GROQ_MODEL`` env var (or ``llama3-8b-8192``).
    system : str  (optional)
        Optional system prompt to prepend to the conversation.

    Response body (JSON)
    --------------------
    reply : str
        The model's text reply.
    model : str
        The model that was used.
    """
    if _groq_client is None:
        return jsonify({"error": _groq_init_error}), 503

    data = request.get_json(silent=True)
    if not data or not data.get("message", "").strip():
        return jsonify({"error": "Request body must include a non-empty 'message' field."}), 400

    user_message: str = data["message"].strip()
    model: str = data.get("model") or _DEFAULT_MODEL
    system_prompt: str = str(data.get("system", ""))
    resonate: bool = bool(data.get("resonate", True))
    include_translation: bool = bool(data.get("include_translation", False))

    expr = _translator.translate(user_message) if resonate else None
    translated_message = expr.to_ai_language() if expr else user_message

    messages = []
    if resonate and not system_prompt:
        system_prompt = (
            "You receive structured task instructions. Follow the INSTRUCTION "
            "section first, use CONTEXT values, and keep answers practical."
        )
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": translated_message})

    try:
        completion = _groq_client.chat.completions.create(
            model=model,
            messages=messages,
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Groq API error: {exc}"}), 502

    reply = completion.choices[0].message.content
    payload: dict[str, Any] = {"reply": reply, "model": model}
    if include_translation and expr is not None:
        payload["translation"] = expr.to_dict()
        payload["ai_message"] = translated_message
    return jsonify(payload), 200


@app.route("/health", methods=["GET"])
def health() -> tuple:
    """Simple health-check endpoint."""
    return jsonify(
        {
            "status": "ok",
            "groq_ready": _groq_client is not None,
            "api_key_protected": bool(_BACKEND_API_KEY),
        }
    ), 200


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=debug)
