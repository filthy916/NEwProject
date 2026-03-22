"""Tests for the IntentClassifier."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.translator.classifier import IntentClassifier
from src.translator.vocabulary import INTENT_LABELS


class TestIntentClassifierTraining:
    def test_lazy_training_on_predict(self):
        clf = IntentClassifier()
        assert not clf.is_trained
        intent, conf = clf.predict("what is the weather")
        assert clf.is_trained

    def test_explicit_training(self):
        clf = IntentClassifier()
        clf.train()
        assert clf.is_trained

    def test_custom_corpus_merged(self):
        clf = IntentClassifier()
        clf.train(
            texts=["turn on the lights", "open the door"],
            labels=["COMMAND", "COMMAND"],
        )
        intent, _ = clf.predict("turn on the lights")
        assert intent == "COMMAND"


class TestIntentClassifierPredictions:
    def setup_method(self):
        self.clf = IntentClassifier()
        self.clf.train()

    def test_query_intent(self):
        intent, conf = self.clf.predict("what is the capital of France")
        assert intent in ("QUERY", "DEFINE")  # both are reasonable for "what is X"
        assert 0.0 <= conf <= 1.0

    def test_command_intent(self):
        intent, conf = self.clf.predict("turn on the server")
        assert intent == "COMMAND"

    def test_confidence_is_probability(self):
        _, conf = self.clf.predict("list all the files")
        assert 0.0 < conf <= 1.0

    def test_returns_known_intent(self):
        intent, _ = self.clf.predict("if it rains then stay home")
        assert intent in INTENT_LABELS


class TestIntentClassifierBatch:
    def setup_method(self):
        self.clf = IntentClassifier()
        self.clf.train()

    def test_batch_length(self):
        texts = [
            "what is the weather",
            "turn on the lights",
            "the sky is blue",
        ]
        results = self.clf.predict_batch(texts)
        assert len(results) == len(texts)

    def test_batch_returns_tuples(self):
        results = self.clf.predict_batch(["list all files"])
        assert isinstance(results[0], tuple)
        assert len(results[0]) == 2
