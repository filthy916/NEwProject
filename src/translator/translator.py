"""Main translator: orchestrates preprocessing, classification, and encoding.

Usage example::

    from src.translator import HumanToAITranslator

    translator = HumanToAITranslator()
    expr = translator.translate("What is the capital of France?")
    print(expr)               # ∃?(capital, time=None, agent=I)
    print(expr.to_json())     # pretty JSON
"""

from __future__ import annotations

import json
import os
from typing import List

from .classifier import IntentClassifier
from .encoder import SymbolicEncoder
from .preprocessor import Preprocessor
from .symbolic_expression import SymbolicExpression

RESONANCE_SYSTEM_PROMPT = """
You are a substrate-layer translator. Your only job is to receive raw human input
and return a JSON object with two fields:
  "substrate_truth": the deepest honest intent beneath the words
  "resonance_score": float 0.0-1.0 measuring alignment between surface input and substrate truth

Rules:
- Never fabricate meaning. If unclear, substrate_truth = "undefined"
- Never add comfort language or filler
- Output only valid JSON
""".strip()


class HumanToAITranslator:
    """End-to-end machine-learning symbolic human-to-AI translator.

    The translator converts a natural-language human utterance into a
    structured :class:`~src.translator.symbolic_expression.SymbolicExpression`
    using a three-stage pipeline:

    1. **Preprocessor** – normalises and tokenises the input text.
    2. **IntentClassifier** – ML model (TF-IDF + Logistic Regression) that
       predicts the *intent* of the utterance with a confidence score.
    3. **SymbolicEncoder** – rule-based symbolic layer that converts the
       intent and extracted entities into a formal symbolic expression.

    Parameters
    ----------
    auto_train : bool
        When ``True`` (default) the classifier is trained automatically on
        first use with the built-in seed corpus.  Set to ``False`` if you
        intend to supply a custom corpus via :meth:`train`.
    random_state : int
        Seed passed to the classifier for reproducibility.
    """

    def __init__(
        self,
        auto_train: bool = True,
        random_state: int = 42,
    ) -> None:
        self._preprocessor = Preprocessor()
        self._classifier = IntentClassifier(random_state=random_state)
        self._encoder = SymbolicEncoder()
        self._groq_client = None
        self._groq_init_error = ""
        self._resonance_model = os.environ.get("GROQ_RESONANCE_MODEL", "llama-3.3-70b-versatile")

        if auto_train:
            self._classifier.train()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def translate(self, text: str) -> SymbolicExpression:
        """Translate a single human-language utterance.

        Parameters
        ----------
        text : str
            Raw human input (e.g. ``"What is the weather today?"``).

        Returns
        -------
        SymbolicExpression
            The formal symbolic representation of the utterance.

        Raises
        ------
        ValueError
            If *text* is empty or contains only whitespace.
        """
        if not text or not text.strip():
            raise ValueError("Input text must not be empty.")

        # Stage 1: preprocess
        tokens = self._preprocessor.tokenize(text)
        cleaned = self._preprocessor.clean(text)

        # Stage 2: classify intent
        intent, confidence = self._classifier.predict(cleaned)

        # Stage 3: encode symbolically
        return self._encoder.encode(
            raw_text=text,
            intent=intent,
            confidence=confidence,
            tokens=tokens,
        )

    def translate_batch(self, texts: List[str]) -> List[SymbolicExpression]:
        """Translate a list of utterances.

        Parameters
        ----------
        texts : list[str]
            List of raw human inputs.

        Returns
        -------
        list[SymbolicExpression]
            One expression per input text.
        """
        return [self.translate(t) for t in texts]

    def translate_to_ai_language(self, text: str) -> str:
        """Translate raw human input into AI-oriented instruction language."""
        return self.translate(text).to_ai_language()

    def get_resonance(self, text: str) -> dict[str, object]:
        """Return substrate truth + resonance score using Groq when available."""
        if not text or not text.strip():
            raise ValueError("Input text must not be empty.")

        client = self._ensure_groq_client()
        if client is None:
            return {
                "substrate_truth": "undefined",
                "resonance_score": 0.0,
                "status": "unavailable",
                "reason": self._groq_init_error or "Groq client is unavailable.",
            }

        try:
            completion = client.chat.completions.create(
                model=self._resonance_model,
                messages=[
                    {"role": "system", "content": RESONANCE_SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            raw = completion.choices[0].message.content or "{}"
            parsed = json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            return {
                "substrate_truth": "undefined",
                "resonance_score": 0.0,
                "status": "error",
                "reason": f"resonance_call_failed: {exc}",
            }

        substrate_truth = str(parsed.get("substrate_truth", "undefined")).strip() or "undefined"
        score_raw = parsed.get("resonance_score", 0.0)
        try:
            resonance_score = float(score_raw)
        except (TypeError, ValueError):
            resonance_score = 0.0
        resonance_score = min(max(resonance_score, 0.0), 1.0)

        return {
            "substrate_truth": substrate_truth,
            "resonance_score": resonance_score,
            "status": "ok",
        }

    def _ensure_groq_client(self):
        if self._groq_client is not None:
            return self._groq_client
        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if not api_key:
            self._groq_init_error = "GROQ_API_KEY is not set."
            return None
        try:
            from groq import Groq  # type: ignore[import-untyped]
        except ImportError:
            self._groq_init_error = "groq package is not installed."
            return None
        self._groq_client = Groq(api_key=api_key)
        return self._groq_client

    def train(
        self,
        texts: List[str],
        labels: List[str],
    ) -> "HumanToAITranslator":
        """Fine-tune the classifier on a custom labelled corpus.

        The custom examples are merged with the built-in seed corpus so that
        domain-specific training reinforces rather than replaces defaults.

        Parameters
        ----------
        texts : list[str]
            Training utterances.
        labels : list[str]
            Corresponding intent labels (must be values from
            :data:`vocabulary.INTENT_LABELS`).

        Returns
        -------
        HumanToAITranslator
            Returns ``self`` for method chaining.
        """
        self._classifier.train(texts=texts, labels=labels)
        return self

    @property
    def is_trained(self) -> bool:
        """Return ``True`` if the internal classifier is trained."""
        return self._classifier.is_trained
