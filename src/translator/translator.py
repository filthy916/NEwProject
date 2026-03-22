"""Main translator: orchestrates preprocessing, classification, and encoding.

Usage example::

    from src.translator import HumanToAITranslator

    translator = HumanToAITranslator()
    expr = translator.translate("What is the capital of France?")
    print(expr)               # ∃?(capital, time=None, agent=I)
    print(expr.to_json())     # pretty JSON
"""

from __future__ import annotations

from typing import List

from .classifier import IntentClassifier
from .encoder import SymbolicEncoder
from .preprocessor import Preprocessor
from .symbolic_expression import SymbolicExpression


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
