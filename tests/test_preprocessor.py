"""Tests for the Preprocessor class."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.translator.preprocessor import Preprocessor


class TestPreprocessorClean:
    def setup_method(self):
        self.pp = Preprocessor()

    def test_lowercase(self):
        assert self.pp.clean("Hello World") == "hello world"

    def test_punctuation_removed(self):
        result = self.pp.clean("Hello, world!")
        assert "," not in result
        assert "!" not in result

    def test_contraction_expansion(self):
        assert "not" in self.pp.clean("it's not working")

    def test_extra_whitespace(self):
        assert self.pp.clean("  too   many   spaces  ") == "too many spaces"

    def test_empty_string(self):
        assert self.pp.clean("") == ""

    def test_contraction_priority_wont(self):
        assert self.pp.clean("won't run") == "will not run"

    def test_contraction_priority_cant(self):
        assert self.pp.clean("can't find it") == "cannot find it"

    def test_slang_normalization(self):
        assert self.pp.clean("wats weather tdy") == "what is weather today"


class TestPreprocessorTokenize:
    def setup_method(self):
        self.pp = Preprocessor()

    def test_returns_list(self):
        assert isinstance(self.pp.tokenize("hello world"), list)

    def test_stop_words_removed(self):
        tokens = self.pp.tokenize("what is the weather today")
        assert "the" not in tokens
        assert "is" not in tokens

    def test_meaningful_tokens_kept(self):
        tokens = self.pp.tokenize("find the weather forecast")
        assert "weather" in tokens
        assert "forecast" in tokens

    def test_empty_input(self):
        assert self.pp.tokenize("") == []

    def test_raw_keeps_stopwords(self):
        tokens = self.pp.tokenize_raw("what is the weather today")
        assert "the" in tokens

    def test_negation_words_preserved(self):
        tokens = self.pp.tokenize("no answer")
        assert "no" in tokens


class TestPreprocessorNoStopwords:
    def test_keep_stop_words_when_disabled(self):
        pp = Preprocessor(remove_stopwords=False)
        tokens = pp.tokenize("what is the weather")
        assert "the" in tokens
        assert "is" in tokens
