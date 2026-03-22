"""Symbolic encoder: maps extracted tokens to a :class:`SymbolicExpression`.

This module is the "symbolic" half of the translator.  After the ML
classifier determines the *intent*, the encoder:

1. Extracts entities (time, quantity, location, agent) from the tokens.
2. Identifies the primary subject of the utterance.
3. Assembles a :class:`SymbolicExpression` with the formal predicate,
   subject, and semantic arguments.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .symbolic_expression import SymbolicExpression
from .vocabulary import (
    ENTITY_PATTERNS,
    INTENT_TO_PREDICATE,
    STOP_WORDS,
)


class SymbolicEncoder:
    """Convert intent + token sequence into a :class:`SymbolicExpression`."""

    # Words that indicate negation even without a "NEGATE" intent
    _NEGATION_WORDS = frozenset({"not", "never", "no", "neither", "nor"})

    # Action verbs commonly found in COMMAND utterances
    _ACTION_VERBS = frozenset({
        "open", "close", "start", "stop", "run", "create", "delete",
        "add", "remove", "set", "enable", "disable", "find", "search",
        "compute", "calculate", "convert", "show", "turn", "execute",
        "send", "move", "copy", "rename", "update", "download",
    })

    def encode(
        self,
        raw_text: str,
        intent: str,
        confidence: float,
        tokens: List[str],
    ) -> SymbolicExpression:
        """Build a :class:`SymbolicExpression` from classifier output.

        Parameters
        ----------
        raw_text : str
            The original human-language input.
        intent : str
            Intent label from the classifier (e.g. ``"QUERY"``).
        confidence : float
            Classifier confidence score.
        tokens : list[str]
            Preprocessed tokens (stop words removed).

        Returns
        -------
        SymbolicExpression
        """
        predicate = INTENT_TO_PREDICATE.get(intent, "?")
        entities = self._extract_entities(tokens)
        subject = self._extract_subject(intent, tokens, entities)
        arguments = self._build_arguments(intent, tokens, entities)

        return SymbolicExpression(
            predicate=predicate,
            intent=intent,
            subject=subject,
            arguments=arguments,
            confidence=confidence,
            raw_text=raw_text,
        )

    # ------------------------------------------------------------------
    # Entity extraction
    # ------------------------------------------------------------------

    def _extract_entities(
        self, tokens: List[str]
    ) -> Dict[str, List[str]]:
        """Return a mapping of entity_type → [matched_tokens]."""
        found: Dict[str, List[str]] = {etype: [] for etype in ENTITY_PATTERNS}
        for token in tokens:
            for etype, patterns in ENTITY_PATTERNS.items():
                if token in patterns:
                    found[etype].append(token)
        return {k: v for k, v in found.items() if v}

    # ------------------------------------------------------------------
    # Subject extraction
    # ------------------------------------------------------------------

    def _extract_subject(
        self,
        intent: str,
        tokens: List[str],
        entities: Dict[str, List[str]],
    ) -> str:
        """Heuristically determine the primary subject of the utterance."""
        # For commands the subject is the action verb + its direct object
        if intent == "COMMAND":
            verbs = [t for t in tokens if t in self._ACTION_VERBS]
            if verbs:
                verb = verbs[0]
                vi = tokens.index(verb)
                obj_candidates = [
                    t for t in tokens[vi + 1:]
                    if t not in self._NEGATION_WORDS
                    and t not in ENTITY_PATTERNS.get("AGENT", [])
                ]
                if obj_candidates:
                    return f"{verb}_{obj_candidates[0]}"
                return verb

        # For conditionals pull the antecedent (after "if")
        if intent == "CONDITIONAL":
            if "if" in tokens:
                idx = tokens.index("if")
                after = tokens[idx + 1:]
                if after:
                    return after[0]

        # For definitions the subject is what follows "define" / "meaning"
        if intent == "DEFINE":
            define_triggers = {"define", "meaning", "definition", "term"}
            for i, t in enumerate(tokens):
                if t in define_triggers and i + 1 < len(tokens):
                    return tokens[i + 1]

        # Fall back: first non-entity, non-agent, content token
        agent_tokens = set(ENTITY_PATTERNS.get("AGENT", []))
        for t in tokens:
            if (
                t not in self._NEGATION_WORDS
                and t not in agent_tokens
                and t not in STOP_WORDS
                and not t.isdigit()
            ):
                return t

        return tokens[0] if tokens else "unknown"

    # ------------------------------------------------------------------
    # Argument builder
    # ------------------------------------------------------------------

    def _build_arguments(
        self,
        intent: str,
        tokens: List[str],
        entities: Dict[str, List[str]],
    ) -> Dict[str, Any]:
        """Build semantic argument dict from entities and intent cues."""
        args: Dict[str, Any] = {}

        # Attach entity values
        if "TIME" in entities:
            args["time"] = entities["TIME"][0]
        if "LOCATION" in entities:
            args["location"] = entities["LOCATION"][0]
        if "QUANTITY" in entities:
            args["quantity"] = entities["QUANTITY"][0]
        if "AGENT" in entities:
            args["agent"] = entities["AGENT"][0].upper()

        # Negation flag
        if any(t in self._NEGATION_WORDS for t in tokens):
            args["negated"] = True

        # Intent-specific extras
        if intent == "CONDITIONAL":
            args["form"] = "implication"
        elif intent == "COMPARE":
            args["form"] = "comparison"
            # Capture both comparison targets if possible
            non_agent = [
                t for t in tokens
                if t not in ENTITY_PATTERNS.get("AGENT", [])
                and t not in STOP_WORDS
                and t not in {"compare", "difference", "versus", "vs",
                               "better", "worse", "similar", "unlike",
                               "same"}
            ]
            if len(non_agent) >= 2:
                args["lhs"] = non_agent[0]
                args["rhs"] = non_agent[1]
        elif intent == "ENUMERATE":
            args["form"] = "list"

        return args
