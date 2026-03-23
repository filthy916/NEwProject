"""ML-based intent classifier.

Uses a TF-IDF vectoriser combined with a Logistic Regression model trained on
a seed corpus generated from the :mod:`vocabulary` intent keyword lists.  The
model is trained lazily on first use and can be retrained on custom corpora.
"""

from __future__ import annotations

import random
from typing import List, Tuple

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from .vocabulary import INTENT_LABELS, INTENT_SEEDS


# ---------------------------------------------------------------------------
# Seed corpus builder
# ---------------------------------------------------------------------------

def _build_seed_corpus() -> Tuple[List[str], List[str]]:
    """Generate a balanced training corpus from :data:`INTENT_SEEDS`.

    For each intent we produce the seed phrases directly and then augment
    them with simple sentence templates to give the classifier enough variety.
    """
    templates = [
        "{phrase} the data",
        "{phrase} this information",
        "{phrase} your name",
        "{phrase} the temperature",
        "{phrase} the server",
        "{phrase} the file",
        "please {phrase} all records",
        "can you {phrase} the result",
        "i want to {phrase} the list",
        "i need you to {phrase} this",
        "{phrase} the configuration",
        "{phrase} the output",
        "{phrase} my account",
        "{phrase} the process",
        "{phrase} everything",
    ]

    texts: List[str] = []
    labels: List[str] = []

    for intent, seeds in INTENT_SEEDS.items():
        for seed in seeds:
            texts.append(seed)
            labels.append(intent)
            for template in random.sample(templates, k=min(5, len(templates))):
                texts.append(template.format(phrase=seed))
                labels.append(intent)

    return texts, labels


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

class IntentClassifier:
    """TF-IDF + Logistic Regression intent classifier.

    The classifier is trained once on a synthetic seed corpus and then
    can be fine-tuned with :meth:`train` on domain-specific examples.

    Parameters
    ----------
    random_state : int
        Random seed for reproducibility.
    """

    def __init__(self, random_state: int = 42) -> None:
        self.random_state = random_state
        self._label_encoder = LabelEncoder()
        self._pipeline: Pipeline | None = None
        self._trained: bool = False

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(
        self,
        texts: List[str] | None = None,
        labels: List[str] | None = None,
    ) -> "IntentClassifier":
        """Train (or retrain) the classifier.

        If *texts* and *labels* are ``None`` the built-in seed corpus is
        used.  Otherwise the provided corpus is merged with the seed corpus
        so that custom examples reinforce rather than replace the defaults.

        Parameters
        ----------
        texts : list[str] | None
            Training sentences.
        labels : list[str] | None
            Corresponding intent labels from :data:`vocabulary.INTENT_LABELS`.

        Returns
        -------
        IntentClassifier
            Returns ``self`` for method chaining.
        """
        seed_texts, seed_labels = _build_seed_corpus()

        if texts is not None and labels is not None:
            combined_texts = seed_texts + list(texts)
            combined_labels = seed_labels + list(labels)
        else:
            combined_texts = seed_texts
            combined_labels = seed_labels

        self._label_encoder.fit(INTENT_LABELS)

        self._pipeline = Pipeline([
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 3),
                    min_df=1,
                    sublinear_tf=True,
                    analyzer="word",
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    random_state=self.random_state,
                    C=1.0,
                    solver="lbfgs",
                ),
            ),
        ])

        self._pipeline.fit(combined_texts, combined_labels)
        self._trained = True
        return self

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(self, text: str) -> Tuple[str, float]:
        """Return ``(intent_label, confidence)`` for *text*.

        The model is trained lazily if :meth:`train` has not yet been called.

        Parameters
        ----------
        text : str
            Raw or preprocessed human-language text.

        Returns
        -------
        tuple[str, float]
            The predicted intent label and the probability score.
        """
        if not self._trained:
            self.train()

        proba = self._pipeline.predict_proba([text])[0]
        classes = self._pipeline.classes_
        idx = int(np.argmax(proba))
        return str(classes[idx]), float(proba[idx])

    def predict_batch(self, texts: List[str]) -> List[Tuple[str, float]]:
        """Batch version of :meth:`predict`."""
        if not self._trained:
            self.train()

        proba_matrix = self._pipeline.predict_proba(texts)
        classes = self._pipeline.classes_
        results = []
        for proba in proba_matrix:
            idx = int(np.argmax(proba))
            results.append((str(classes[idx]), float(proba[idx])))
        return results

    @property
    def is_trained(self) -> bool:
        """Return ``True`` if the classifier has been trained."""
        return self._trained
