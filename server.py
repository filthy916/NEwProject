"""Flask backend server — exposes a /api/chat endpoint backed by Groq.

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

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request

# Load variables from a local .env file (ignored by git) if present.
# Variables already set in the environment take precedence.
load_dotenv()

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Groq client — initialised once at startup
# ---------------------------------------------------------------------------

_GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
if not _GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY environment variable is not set. "
        "Copy .env.example to .env and add your key."
    )

try:
    from groq import Groq  # type: ignore[import-untyped]
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The 'groq' package is not installed. Run: pip install groq"
    ) from exc

_groq_client = Groq(api_key=_GROQ_API_KEY)

_DEFAULT_MODEL = os.environ.get("GROQ_MODEL", "llama3-8b-8192")

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


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
    data = request.get_json(silent=True)
    if not data or not data.get("message", "").strip():
        return jsonify({"error": "Request body must include a non-empty 'message' field."}), 400

    user_message: str = data["message"].strip()
    model: str = data.get("model") or _DEFAULT_MODEL
    system_prompt: str = data.get("system", "")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})

    try:
        completion = _groq_client.chat.completions.create(
            model=model,
            messages=messages,
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Groq API error: {exc}"}), 502

    reply = completion.choices[0].message.content
    return jsonify({"reply": reply, "model": model}), 200


@app.route("/health", methods=["GET"])
def health() -> tuple:
    """Simple health-check endpoint."""
    return jsonify({"status": "ok"}), 200


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=debug)
