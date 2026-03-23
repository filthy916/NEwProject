"""Symbolic expression: the structured output of the translator.

A :class:`SymbolicExpression` represents a human utterance in a formal,
AI-readable form consisting of:

* **predicate** – the high-level operator (e.g. ``∃?`` for a query)
* **intent** – the human-readable intent label (e.g. ``QUERY``)
* **subject** – the main noun / topic
* **arguments** – additional key→value semantic arguments
* **confidence** – ML model confidence in [0, 1]

The expression can be serialised to a string, a dict, or JSON.
"""

from __future__ import annotations

import json
from typing import Any


class SymbolicExpression:
    """Formal symbolic representation of a human utterance.

    Parameters
    ----------
    predicate : str
        Formal symbolic operator (e.g. ``∃?``, ``DO``, ``⊨``).
    intent : str
        Human-readable intent label (e.g. ``QUERY``, ``COMMAND``).
    subject : str
        Primary topic or object extracted from the text.
    arguments : dict[str, Any]
        Additional semantic arguments (entities, relations, etc.).
    confidence : float
        Classifier confidence score in the range ``[0.0, 1.0]``.
    raw_text : str
        Original human input that produced this expression.
    """

    def __init__(
        self,
        predicate: str,
        intent: str,
        subject: str,
        arguments: dict[str, Any],
        confidence: float,
        raw_text: str,
    ) -> None:
        self.predicate = predicate
        self.intent = intent
        self.subject = subject
        self.arguments = arguments
        self.confidence = round(float(confidence), 4)
        self.raw_text = raw_text

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a plain-dict representation suitable for JSON export."""
        return {
            "predicate": self.predicate,
            "intent": self.intent,
            "subject": self.subject,
            "arguments": self.arguments,
            "confidence": self.confidence,
            "raw_text": self.raw_text,
        }

    def to_json(self, indent: int = 2) -> str:
        """Return a pretty-printed JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_symbolic_string(self) -> str:
        """Return a compact S-expression–style symbolic string.

        Example output::

            ∃?(weather, time=today, agent=I)
        """
        args_str = ", ".join(
            f"{k}={v}" for k, v in self.arguments.items() if v
        )
        if args_str:
            return f"{self.predicate}({self.subject}, {args_str})"
        if self.subject:
            return f"{self.predicate}({self.subject})"
        return f"{self.predicate}()"

    def to_ai_language(self) -> str:
        """Return an AI-oriented instruction block derived from this expression.

        The output is deterministic and structured so it can be passed directly
        to an LLM as a rewritten, intent-explicit version of the human input.
        """
        normalized_subject = self.subject.replace("_", " ").strip() or "unknown"

        # Deterministic argument ordering keeps output stable across runs.
        context_lines = []
        for key in sorted(self.arguments):
            value = self.arguments[key]
            if value not in (None, "", []):
                context_lines.append(f"- {key}: {value}")
        context_text = "\n".join(context_lines) if context_lines else "- none"

        instruction = self._build_ai_instruction(normalized_subject)

        return (
            f"TASK_INTENT: {self.intent}\n"
            f"PRIMARY_SUBJECT: {normalized_subject}\n"
            f"CONFIDENCE: {self.confidence:.4f}\n"
            f"CONTEXT:\n{context_text}\n"
            f"INSTRUCTION:\n{instruction}\n"
            f"ORIGINAL_INPUT: {self.raw_text}"
        )

    def _build_ai_instruction(self, subject: str) -> str:
        """Build an intent-aware instruction sentence for LLM consumption."""
        if self.intent == "QUERY":
            return (
                f"Answer the user's question about '{subject}' with factual, "
                "concise, and directly useful information."
            )
        if self.intent == "COMMAND":
            return (
                f"Execute or outline the action '{subject}'. If critical "
                "details are missing, ask one focused follow-up question."
            )
        if self.intent == "ASSERT":
            return (
                f"Evaluate the statement about '{subject}' and respond with a "
                "clear confirmation or correction."
            )
        if self.intent == "CONDITIONAL":
            return (
                f"Reason about the condition involving '{subject}' and explain "
                "the likely outcome in a clear cause-and-effect form."
            )
        if self.intent == "NEGATE":
            return (
                f"Respect the negated request about '{subject}' and avoid "
                "contradicting the user's stated constraint."
            )
        if self.intent == "COMPARE":
            lhs = self.arguments.get("lhs")
            rhs = self.arguments.get("rhs")
            if lhs and rhs:
                return (
                    f"Compare '{lhs}' and '{rhs}' using concrete tradeoffs and "
                    "end with a practical recommendation."
                )
            return (
                f"Provide a comparison centered on '{subject}' with concrete "
                "tradeoffs and a practical recommendation."
            )
        if self.intent == "DEFINE":
            return (
                f"Provide a simple, accurate definition of '{subject}', then "
                "add one quick real-world example."
            )
        if self.intent == "ENUMERATE":
            return (
                f"Return a concise list of items related to '{subject}' in a "
                "clean, readable format."
            )
        return (
            f"Interpret and respond to the request about '{subject}' with a "
            "direct and helpful answer."
        )

    # ------------------------------------------------------------------
    # Magic methods
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return self.to_symbolic_string()

    def __repr__(self) -> str:
        return (
            f"SymbolicExpression(intent={self.intent!r}, "
            f"subject={self.subject!r}, "
            f"confidence={self.confidence})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SymbolicExpression):
            return NotImplemented
        return self.to_dict() == other.to_dict()
