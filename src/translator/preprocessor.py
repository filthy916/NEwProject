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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def clean(self, text: str) -> str:
        """Return a normalised version of *text* (no tokenisation)."""
        if self.lowercase:
            text = text.lower()
        text = self._expand_contractions(text)
        text = self._punctuation_re.sub(" ", text)
        text = self._whitespace_re.sub(" ", text).strip()
        return text

    def tokenize(self, text: str) -> List[str]:
        """Return a list of meaningful tokens from *text*."""
        cleaned = self.clean(text)
        tokens = cleaned.split()
        if self.remove_stopwords:
            tokens = [t for t in tokens if t not in STOP_WORDS]
        return [t for t in tokens if t]  # drop empty strings

    def tokenize_raw(self, text: str) -> List[str]:
        """Return *all* tokens (stop words included) after cleaning."""
        cleaned = self.clean(text)
        return [t for t in cleaned.split() if t]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _expand_contractions(text: str) -> str:
        """Expand common English contractions."""
        contractions = {
            "n't": " not",
            "'re": " are",
            "'s": " is",
            "'ll": " will",
            "'d": " would",
            "'ve": " have",
            "'m": " am",
            "won't": "will not",
            "can't": "cannot",
            "i'm": "i am",
            "let's": "let us",
        }
        for pattern, replacement in contractions.items():
            text = text.replace(pattern, replacement)
        return text
