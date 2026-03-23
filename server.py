"""1ONE backend: single-turn human/AI bridge with strict auth."""

from __future__ import annotations

import hmac
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from src.translator import (
    HumanToAITranslator,
    ai_to_human_format,
    detect_refusal_or_echo,
    normalize_text,
    retrieve_grounding,
    verify_reply,
)
from werkzeug.exceptions import HTTPException

load_dotenv()

APP_NAME = "1ONE"
FRONTEND_DIR = Path(__file__).parent / "frontend"

app = Flask(__name__)
_translator = HumanToAITranslator()

_GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
_DEFAULT_MODEL = os.environ.get("GROQ_MODEL", "llama3-8b-8192")
_BRIDGE_SECRET = os.environ.get("BRIDGE_SECRET_916", "").strip()

_groq_client = None
_groq_init_error = ""
if _GROQ_API_KEY:
    try:
        from groq import Groq  # type: ignore[import-untyped]
    except ImportError:
        _groq_init_error = "The 'groq' package is not installed. Run: pip install groq"
    else:
        _groq_client = Groq(api_key=_GROQ_API_KEY)
else:
    _groq_init_error = (
        "GROQ_API_KEY environment variable is not set. "
        "Copy .env.example to .env and add your key."
    )


def _json_response(payload: dict[str, Any], status: int = 200):
    body = dict(payload)
    body.setdefault("app", APP_NAME)
    response = jsonify(body)
    response.status_code = status
    response.headers["X-App-Name"] = APP_NAME
    return response


def _extract_secret() -> str:
    for header in ("X-Auth-Secret", "X-API-Key"):
        value = request.headers.get(header, "").strip()
        if value:
            return value
    auth = request.headers.get("Authorization", "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return auth


def _parse_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _clamp_retries(value: Any) -> int:
    try:
        retries = int(value)
    except (TypeError, ValueError):
        retries = 3
    return max(1, min(retries, 3))


def _provider_generate(
    provider: str,
    model: str,
    direction: str,
    normalized_input: str,
    resonant_prompt: str,
    style: str,
    attempt: int,
) -> tuple[str, str | None]:
    if provider != "groq":
        return "", f"Unsupported provider: {provider}"
    if _groq_client is None:
        return "", _groq_init_error or "Groq provider is unavailable."

    if direction == "human_to_ai":
        system_prompt = (
            f"You are {APP_NAME}. Convert human intent into concise AI-ready instructions. "
            "Be direct and specific."
        )
    else:
        system_prompt = (
            f"You are {APP_NAME}. Translate machine-style output into clear human language "
            "without removing important technical meaning."
        )
    if attempt > 1:
        system_prompt += " Previous attempt was weak. Avoid echo and vague filler."

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"Direction: {direction}\n"
                f"Style: {style}\n"
                f"Original input:\n{normalized_input}\n\n"
                f"Bridge prompt:\n{resonant_prompt}"
            ),
        },
    ]

    try:
        completion = _groq_client.chat.completions.create(model=model, messages=messages)
    except Exception as exc:  # noqa: BLE001
        app.logger.warning("Groq provider failure on attempt %s: %s", attempt, exc)
        return "", "Groq provider request failed."

    reply = completion.choices[0].message.content or ""
    return reply.strip(), None


@app.before_request
def require_api_secret():
    if request.path == "/health" or not request.path.startswith("/api/"):
        return None
    if not _BRIDGE_SECRET:
        return _json_response(
            {"error": "Server misconfiguration: BRIDGE_SECRET_916 is not set."},
            status=503,
        )
    provided = _extract_secret()
    if not provided or not hmac.compare_digest(provided, _BRIDGE_SECRET):
        return _json_response({"error": "Unauthorized"}, status=401)
    return None


@app.errorhandler(Exception)
def handle_unexpected_error(exc: Exception):
    if isinstance(exc, HTTPException):
        return _json_response({"error": exc.description}, status=int(exc.code or 500))
    app.logger.exception("Unhandled server exception: %s", exc)
    return _json_response({"error": "Internal server error"}, status=500)


@app.route("/api/bridge", methods=["POST"])
def bridge():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return _json_response({"error": "Request body must include non-empty 'text'."}, 400)

    direction = str(data.get("direction", "human_to_ai")).strip().lower()
    if direction not in {"human_to_ai", "ai_to_human"}:
        return _json_response(
            {"error": "Invalid direction. Use 'human_to_ai' or 'ai_to_human'."},
            400,
        )

    provider = str(data.get("provider", "groq")).strip().lower()
    output_format = str(data.get("format", "json")).strip().lower()
    if output_format not in {"json", "text"}:
        return _json_response({"error": "Invalid format. Use 'json' or 'text'."}, 400)

    max_retries = _clamp_retries(data.get("max_retries"))
    model = str(data.get("model") or _DEFAULT_MODEL).strip()

    normalized_meta = normalize_text(text)
    normalized_input = str(normalized_meta["normalized"])
    style = str(normalized_meta["style"])
    decode_steps = normalized_meta.get("steps", [])
    decoded_as = decode_steps[0] if decode_steps else None
    grounding_evidence = retrieve_grounding(normalized_input)

    if direction == "human_to_ai":
        expr = _translator.translate(normalized_input)
        intent = expr.intent
        resonant_prompt = expr.to_ai_language()
    else:
        intent = "EXPLAIN"
        resonant_prompt = ai_to_human_format(normalized_input)

    attempts: List[Dict[str, Any]] = []
    raw_reply = ""
    resonant_reply = resonant_prompt
    refusal_detected = False
    verified = False
    last_error: str | None = None

    for attempt in range(1, max_retries + 1):
        raw_candidate = resonant_prompt if direction == "human_to_ai" else normalized_input
        provider_error: str | None = None

        if provider == "groq" and _groq_client is not None:
            candidate, provider_error = _provider_generate(
                provider=provider,
                model=model,
                direction=direction,
                normalized_input=normalized_input,
                resonant_prompt=resonant_prompt,
                style=style,
                attempt=attempt,
            )
            if candidate:
                raw_candidate = candidate
        elif provider != "groq":
            provider_error = f"Unsupported provider: {provider}"

        resonant_candidate = (
            raw_candidate if direction == "human_to_ai" else ai_to_human_format(raw_candidate)
        )
        refusal, echo = detect_refusal_or_echo(resonant_candidate, normalized_input)
        attempt_verified = verify_reply(resonant_candidate) and not echo
        attempt_status = "ok" if attempt_verified else "retry_needed"
        if provider_error and not attempt_verified:
            attempt_status = "provider_error"
        attempts.append(
            {
                "number": attempt,
                "status": attempt_status,
                "refusal": refusal,
                "echo": echo,
                "provider_error": provider_error,
                "reply": raw_candidate,
                "resonant_reply": resonant_candidate,
            }
        )

        raw_reply = raw_candidate
        resonant_reply = resonant_candidate
        refusal_detected = refusal_detected or refusal or echo

        if attempt_verified:
            verified = True
            last_error = provider_error
            break
        if provider_error:
            last_error = provider_error

    if verified:
        final_status = "ok"
    else:
        final_status = "retry_exhausted" if attempts else "provider_unavailable"
        if provider == "groq" and _groq_client is None and not attempts:
            last_error = _groq_init_error or "Groq provider is unavailable."

    payload: dict[str, Any] = {
        "direction": direction,
        "provider": provider,
        "model": model,
        "normalized_input": normalized_input,
        "intent": intent,
        "attempts": attempts,
        "final_status": final_status,
        "refusal_detected": refusal_detected,
        "verified": verified,
        "grounding_evidence": grounding_evidence,
        "resonant_reply": resonant_reply,
        "raw_reply": raw_reply,
        "style": style,
        "decoded_as": decoded_as,
    }
    if last_error:
        payload["provider_error"] = last_error
    if output_format == "text":
        payload["resonant_reply"] = ai_to_human_format(resonant_reply)

    status_code = 502 if final_status == "provider_unavailable" else 200
    return _json_response(payload, status_code)


@app.route("/api/translate", methods=["POST"])
def translate():
    data = request.get_json(silent=True) or {}
    source_text = str(data.get("text") or data.get("message") or "").strip()
    if not source_text:
        return _json_response(
            {"error": "Request body must include a non-empty 'text' field."}, 400
        )

    fmt = str(data.get("format", "ai")).lower()
    if fmt not in {"symbolic", "dict", "json", "ai"}:
        return _json_response({"error": "Invalid format. Use symbolic, dict, json, or ai."}, 400)

    expr = _translator.translate(source_text)
    resonance = _translator.get_resonance(source_text)
    if fmt == "symbolic":
        translated: Any = str(expr)
    elif fmt == "dict":
        translated = expr.to_dict()
    elif fmt == "json":
        translated = expr.to_json()
    else:
        translated = expr.to_ai_language()

    return _json_response(
        {
            "surface_input": source_text,
            "symbolic": expr.to_dict(),
            "substrate_truth": resonance.get("substrate_truth", "undefined"),
            "resonance_score": resonance.get("resonance_score", 0.0),
            "resonance_status": resonance.get("status", "unknown"),
            "intent": expr.intent,
            "predicate": str(expr),
            "format": fmt,
            "translated": translated,
            "structured": expr.to_dict(),
        },
        200,
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    if _groq_client is None:
        return _json_response({"error": _groq_init_error}, 503)

    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    if not message:
        return _json_response(
            {"error": "Request body must include a non-empty 'message' field."}, 400
        )

    model = str(data.get("model") or _DEFAULT_MODEL).strip()
    system_prompt = str(data.get("system", "")).strip()
    resonate = _parse_bool(data.get("resonate", True), default=True)
    include_translation = _parse_bool(data.get("include_translation", False), default=False)

    expr = _translator.translate(message) if resonate else None
    user_content = expr.to_ai_language() if expr is not None else message

    messages = []
    if resonate and not system_prompt:
        system_prompt = (
            f"{APP_NAME} receives structured instructions. Use INSTRUCTION and CONTEXT first, "
            "then answer directly."
        )
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_content})

    try:
        completion = _groq_client.chat.completions.create(model=model, messages=messages)
    except Exception as exc:  # noqa: BLE001
        app.logger.warning("Groq chat failure: %s", exc)
        return _json_response({"error": "Groq provider request failed."}, 502)

    reply = (completion.choices[0].message.content or "").strip()
    payload: dict[str, Any] = {"reply": reply, "model": model, "provider": "groq"}
    if include_translation and expr is not None:
        payload["translation"] = expr.to_dict()
        payload["ai_message"] = user_content
    return _json_response(payload, 200)


@app.route("/health", methods=["GET"])
def health():
    ready = bool(_BRIDGE_SECRET)
    return _json_response(
        {
            "status": "ok" if ready else "degraded",
            "groq_ready": _groq_client is not None,
            "bridge_secret_protected": bool(_BRIDGE_SECRET),
            "ready": ready,
            "mode": "single_turn",
        },
        200,
    )


@app.route("/", methods=["GET"])
def index():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.is_file():
        return send_from_directory(FRONTEND_DIR, "index.html")
    return _json_response({"message": "Frontend is not available."}, 200)


@app.route("/<path:path>", methods=["GET"])
def frontend_assets(path: str):
    if path.startswith("api/") or path == "health":
        return _json_response({"error": "Not found"}, 404)
    asset = FRONTEND_DIR / path
    if asset.is_file():
        return send_from_directory(FRONTEND_DIR, path)
    index_path = FRONTEND_DIR / "index.html"
    if index_path.is_file():
        return send_from_directory(FRONTEND_DIR, "index.html")
    return _json_response({"error": "Not found"}, 404)


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=debug)
