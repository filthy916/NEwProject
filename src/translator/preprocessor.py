"""Text preprocessor: cleans and tokenises human-language input."""

import re
import string
from typing import List

from .vocabulary import STOP_WORDS


class Preprocessor:
    """Normalise, tokenise, and filter human-language text.

    Parameters
    ----------
    remove_stopwords : bool
        When *True* (default) stop words listed in :mod:`vocabulary` are
        removed from the token list.  Disable if the downstream component
        needs full token coverage.
    lowercase : bool
        Convert all text to lower case before tokenising (default *True*).
    """

    def __init__(
        self,
        remove_stopwords: bool = True,
        lowercase: bool = True,
    ) -> None:
        self.remove_stopwords = remove_stopwords
        self.lowercase = lowercase
        self._punctuation_re = re.compile(
            r"[" + re.escape(string.punctuation.replace("'", "")) + r"]"
        )
        self._whitespace_re = re.compile(r"\s+")
        self._slang_patterns = [
            (re.compile(r"\bwats\b"), "what is"),
            (re.compile(r"\bwat\b"), "what"),
            (re.compile(r"\bwut\b"), "what"),
            (re.compile(r"\bwhats\b"), "what is"),
            (re.compile(r"\bpls\b"), "please"),
            (re.compile(r"\bplz+\b"), "please"),
            (re.compile(r"\bgimme\b"), "give me"),
            (re.compile(r"\blemme\b"), "let me"),
            (re.compile(r"\bcmp\b"), "compare"),
            (re.compile(r"\bdefs\b"), "define"),
            (re.compile(r"\bdefn\b"), "definition"),
            (re.compile(r"\btdy\b"), "today"),
            (re.compile(r"\b2day\b"), "today"),
            (re.compile(r"\btmrw\b"), "tomorrow"),
            (re.compile(r"\btmr\b"), "tomorrow"),
            (re.compile(r"\btomrw\b"), "tomorrow"),
            (re.compile(r"\b2moro\b"), "tomorrow"),
            (re.compile(r"\brn\b"), "now"),
            (re.compile(r"\bmsg\b"), "message"),
            (re.compile(r"\binfo\b"), "information"),
            (re.compile(r"\bhosp\b"), "hospital"),
            (re.compile(r"\bu\b"), "you"),
            (re.compile(r"\bur\b"), "your"),
            (re.compile(r"\br\b"), "are"),
        ]
        # Keep intent-critical words even when stop-word filtering is enabled.
        self._protected_tokens = {"no", "not", "never", "nor", "neither", "if"}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def clean(self, text: str) -> str:
        """Return a normalised version of *text* (no tokenisation)."""
        if self.lowercase:
            text = text.lower()
        text = self._normalize_slang(text)
        text = self._expand_contractions(text)
        text = self._punctuation_re.sub(" ", text)
        text = self._whitespace_re.sub(" ", text).strip()
        return text

    def tokenize(self, text: str) -> List[str]:
        """Return a list of meaningful tokens from *text*."""
        cleaned = self.clean(text)
        tokens = cleaned.split()
        if self.remove_stopwords:
            tokens = [
                t for t in tokens
                if (t not in STOP_WORDS) or (t in self._protected_tokens)
            ]
        return [t for t in tokens if t]  # drop empty strings

    def tokenize_raw(self, text: str) -> List[str]:
        """Return *all* tokens (stop words included) after cleaning."""
        cleaned = self.clean(text)
        return [t for t in cleaned.split() if t]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _normalize_slang(self, text: str) -> str:
        """Normalize common chat slang and abbreviations."""
        normalized = text
        for pattern, replacement in self._slang_patterns:
            normalized = pattern.sub(replacement, normalized)
        return normalized

    @staticmethod
    def _expand_contractions(text: str) -> str:
        """Expand common English contractions."""
        contractions = [
            ("won't", "will not"),
            ("can't", "cannot"),
            ("i'm", "i am"),
            ("let's", "let us"),
            ("n't", " not"),
            ("'re", " are"),
            ("'s", " is"),
            ("'ll", " will"),
            ("'d", " would"),
            ("'ve", " have"),
            ("'m", " am"),
        ]
        for pattern, replacement in contractions:
            text = text.replace(pattern, replacement)
        return text
