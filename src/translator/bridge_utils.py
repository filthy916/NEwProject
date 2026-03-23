"""Utility helpers for the bridge endpoint.

These functions stay intentionally lightweight: they normalise potentially
encoded inputs, perform rough style detection, and provide tiny stubs for
grounding, refusal detection, and AI→human formatting.  They are pure helpers
so they can be unit-tested without network access.
"""

from __future__ import annotations

import base64
import binascii
import json
import re
import string
from typing import Dict, List, Tuple


_PRINTABLE = set(string.printable)


def _is_mostly_printable(text: str, threshold: float = 0.8) -> bool:
    if not text:
        return False
    printable = sum(1 for ch in text if ch in _PRINTABLE)
    return (printable / len(text)) >= threshold


def _try_base64(text: str) -> Tuple[bool, str]:
    try:
        decoded = base64.b64decode(text, validate=True)
        decoded_text = decoded.decode("utf-8")
        if _is_mostly_printable(decoded_text):
            return True, decoded_text
    except (binascii.Error, UnicodeDecodeError, ValueError):
        pass
    return False, text


def _try_hex(text: str) -> Tuple[bool, str]:
    if not re.fullmatch(r"[0-9a-fA-F]+", text) or len(text) % 2 != 0:
        return False, text
    try:
        decoded = bytes.fromhex(text)
        decoded_text = decoded.decode("utf-8")
        if _is_mostly_printable(decoded_text):
            return True, decoded_text
    except (ValueError, UnicodeDecodeError):
        pass
    return False, text


def detect_style(text: str) -> str:
    """Roughly classify the input style to guide downstream handling."""

    stripped = text.strip()
    lowered = stripped.lower()

    if re.fullmatch(r"[01\s]{8,}", stripped):
        return "binary-ish"

    if re.search(r"\b(def|class|function|return|var|const)\b", lowered) or "{" in stripped or ";" in stripped:
        return "code"

    if re.search(r"\bif\b.*\bthen\b", lowered) or "endif" in lowered or "loop" in lowered:
        return "pseudocode"

    return "plain"


def normalize_text(text: str) -> Dict[str, object]:
    """Decode base64/hex when appropriate and label the style.

    Returns a dict with ``normalized`` text, decode ``steps``, and ``style``.
    """

    normalized = text.strip()
    steps: List[str] = []

    decoded, normalized_candidate = _try_base64(normalized)
    if decoded:
        normalized = normalized_candidate.strip()
        steps.append("base64")
    else:
        decoded_hex, normalized_candidate = _try_hex(normalized)
        if decoded_hex:
            normalized = normalized_candidate.strip()
            steps.append("hex")

    style = detect_style(normalized)
    return {"normalized": normalized, "steps": steps, "style": style}


def ai_to_human_format(text: str) -> str:
    """Make an AI-oriented reply friendlier for humans.

    Tries JSON parsing first, then strips translator markers, else returns the
    trimmed text.
    """

    candidate = text.strip()
    try:
        parsed = json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        parsed = None

    if isinstance(parsed, dict):
        return "; ".join(f"{k}: {v}" for k, v in parsed.items())
    if isinstance(parsed, list):
        return ", ".join(str(item) for item in parsed)

    if "TASK_INTENT" in candidate and "INSTRUCTION" in candidate:
        cleaned = re.sub(r"TASK_INTENT:\s*\w+", "", candidate)
        cleaned = cleaned.replace("INSTRUCTION:", "").strip()
        return cleaned

    return candidate


_GROUNDING_GRAPH = {
    "weather": {"keywords": ["weather", "temperature", "forecast"], "evidence": "Use latest local forecast data."},
    "files": {"keywords": ["file", "files", "directory"], "evidence": "List files from the working directory graph."},
    "code": {"keywords": ["code", "function", "bug"], "evidence": "Consult recent code context nodes."},
}


def retrieve_grounding(text: str) -> List[Dict[str, object]]:
    """Return lightweight grounding hints based on keyword hits."""
    lowered = text.lower()
    hits: List[Dict[str, object]] = []

    for node, meta in _GROUNDING_GRAPH.items():
        if any(keyword in lowered for keyword in meta["keywords"]):
            hits.append({"node": node, "evidence": meta["evidence"], "score": 0.71})

    if not hits:
        hits.append({"node": "generic", "evidence": "No strong grounding match; using generic context only.", "score": 0.3})

    return hits


def detect_refusal_or_echo(reply: str, source: str) -> Tuple[bool, bool]:
    """Identify likely refusals or echo responses."""
    lowered = reply.lower()
    refusal_keywords = ["cannot", "can't", "sorry", "unable", "as an ai", "not able"]
    refusal = any(keyword in lowered for keyword in refusal_keywords)
    echo = reply.strip() == source.strip()
    return refusal, echo


def verify_reply(reply: str) -> bool:
    """Stub verifier: non-empty and not a refusal marker."""
    if not reply or not reply.strip():
        return False
    lowered = reply.lower()
    if "cannot" in lowered or "sorry" in lowered:
        return False
    return True


__all__ = [
    "normalize_text",
    "detect_style",
    "ai_to_human_format",
    "retrieve_grounding",
    "detect_refusal_or_echo",
    "verify_reply",
]
