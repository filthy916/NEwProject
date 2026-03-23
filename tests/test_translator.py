"""Integration tests for HumanToAITranslator (end-to-end)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.translator import HumanToAITranslator
from src.translator.symbolic_expression import SymbolicExpression
from src.translator.vocabulary import INTENT_LABELS, INTENT_TO_PREDICATE


@pytest.fixture(scope="module")
def translator():
    """Shared, trained translator to avoid re-training between tests."""
    return HumanToAITranslator()


class TestTranslatorBasic:
    def test_returns_symbolic_expression(self, translator):
        result = translator.translate("What is the weather today?")
        assert isinstance(result, SymbolicExpression)

    def test_empty_input_raises(self, translator):
        with pytest.raises(ValueError):
            translator.translate("")

    def test_whitespace_only_raises(self, translator):
        with pytest.raises(ValueError):
            translator.translate("   ")

    def test_is_trained(self, translator):
        assert translator.is_trained


class TestTranslatorIntents:
    def test_query_sentence(self, translator):
        expr = translator.translate("Where is the nearest hospital?")
        assert expr.intent == "QUERY"
        assert expr.predicate == "∃?"

    def test_command_sentence(self, translator):
        expr = translator.translate("Turn on the lights")
        assert expr.intent == "COMMAND"
        assert expr.predicate == "DO"

    def test_define_sentence(self, translator):
        expr = translator.translate("Define the word entropy")
        assert expr.intent == "DEFINE"

    def test_enumerate_sentence(self, translator):
        expr = translator.translate("List all the files in the directory")
        assert expr.intent == "ENUMERATE"

    def test_compare_sentence(self, translator):
        expr = translator.translate("Compare Python versus JavaScript")
        assert expr.intent == "COMPARE"


class TestTranslatorOutput:
    def test_confidence_in_range(self, translator):
        expr = translator.translate("What is the weather today?")
        assert 0.0 < expr.confidence <= 1.0

    def test_raw_text_preserved(self, translator):
        text = "What is the temperature outside?"
        expr = translator.translate(text)
        assert expr.raw_text == text

    def test_symbolic_string_non_empty(self, translator):
        expr = translator.translate("What is machine learning?")
        assert len(str(expr)) > 0

    def test_to_json_valid(self, translator):
        import json
        expr = translator.translate("Turn off the server")
        data = json.loads(expr.to_json())
        assert "intent" in data
        assert "predicate" in data

    def test_time_entity_extracted(self, translator):
        expr = translator.translate("What is the weather today?")
        args = expr.arguments
        assert args.get("time") == "today"

    def test_translate_to_ai_language(self, translator):
        ai_text = translator.translate_to_ai_language("Turn on the lights")
        assert "TASK_INTENT: COMMAND" in ai_text
        assert "INSTRUCTION:" in ai_text


class TestTranslatorBatch:
    def test_batch_returns_list(self, translator):
        texts = [
            "What is the weather?",
            "Turn on the lights",
            "List all the files",
        ]
        results = translator.translate_batch(texts)
        assert isinstance(results, list)
        assert len(results) == 3

    def test_batch_all_expressions(self, translator):
        texts = ["What is AI?", "Delete the record"]
        results = translator.translate_batch(texts)
        assert all(isinstance(r, SymbolicExpression) for r in results)


class TestTranslatorFineTuning:
    def test_custom_training(self):
        t = HumanToAITranslator()
        t.train(
            texts=["open the window please", "close the door"],
            labels=["COMMAND", "COMMAND"],
        )
        expr = t.translate("open the window please")
        assert expr.intent == "COMMAND"

    def test_method_chaining(self):
        t = HumanToAITranslator(auto_train=False)
        result = t.train(["what is this"], ["QUERY"])
        assert result is t


class TestTranslatorNoisyQueries:
    def test_slang_query_time_entity(self, translator):
        expr = translator.translate("wats weather tdy")
        assert expr.intent == "QUERY"
        assert expr.arguments.get("time") == "today"
        assert expr.subject == "weather"

    def test_short_compare_shorthand(self, translator):
        expr = translator.translate("cmp python vs js")
        assert expr.intent == "COMPARE"
        assert expr.arguments.get("lhs") == "python"
        assert expr.arguments.get("rhs") == "js"

    def test_polite_broken_enumerate(self, translator):
        expr = translator.translate("pls list files")
        assert expr.intent == "ENUMERATE"
        assert expr.subject == "files"

    def test_short_location_abbreviation(self, translator):
        expr = translator.translate("where hosp?")
        assert expr.intent == "QUERY"
        assert expr.subject == "hospital"

    def test_negation_contraction_preserved(self, translator):
        expr = translator.translate("can't find file")
        assert expr.intent == "NEGATE"
        assert expr.arguments.get("negated") is True
