"""Tests for the SymbolicExpression class."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.translator.symbolic_expression import SymbolicExpression


def make_expr(**kwargs):
    defaults = dict(
        predicate="∃?",
        intent="QUERY",
        subject="weather",
        arguments={"time": "today"},
        confidence=0.95,
        raw_text="What is the weather today?",
    )
    defaults.update(kwargs)
    return SymbolicExpression(**defaults)


class TestSymbolicExpressionString:
    def test_symbolic_string_with_args(self):
        expr = make_expr()
        s = expr.to_symbolic_string()
        assert s.startswith("∃?(")
        assert "weather" in s
        assert "time=today" in s

    def test_symbolic_string_no_args(self):
        expr = make_expr(subject="weather", arguments={})
        assert expr.to_symbolic_string() == "∃?(weather)"

    def test_empty_subject_and_args(self):
        expr = make_expr(subject="", arguments={})
        assert expr.to_symbolic_string() == "∃?()"

    def test_str_delegates_to_symbolic_string(self):
        expr = make_expr()
        assert str(expr) == expr.to_symbolic_string()


class TestSymbolicExpressionDict:
    def test_to_dict_keys(self):
        expr = make_expr()
        d = expr.to_dict()
        assert set(d.keys()) == {
            "predicate", "intent", "subject", "arguments",
            "confidence", "raw_text"
        }

    def test_to_dict_values(self):
        expr = make_expr()
        d = expr.to_dict()
        assert d["intent"] == "QUERY"
        assert d["subject"] == "weather"
        assert d["confidence"] == 0.95


class TestSymbolicExpressionJson:
    def test_valid_json(self):
        expr = make_expr()
        data = json.loads(expr.to_json())
        assert data["intent"] == "QUERY"

    def test_json_contains_raw_text(self):
        expr = make_expr()
        assert "What is the weather today?" in expr.to_json()


class TestSymbolicExpressionAiLanguage:
    def test_ai_language_contains_core_sections(self):
        expr = make_expr()
        text = expr.to_ai_language()
        assert "TASK_INTENT: QUERY" in text
        assert "PRIMARY_SUBJECT: weather" in text
        assert "CONTEXT:" in text
        assert "INSTRUCTION:" in text

    def test_compare_instruction_uses_lhs_rhs(self):
        expr = make_expr(
            intent="COMPARE",
            subject="python",
            arguments={"lhs": "python", "rhs": "javascript"},
        )
        text = expr.to_ai_language().lower()
        assert "compare 'python' and 'javascript'" in text


class TestSymbolicExpressionEquality:
    def test_equal_expressions(self):
        a = make_expr()
        b = make_expr()
        assert a == b

    def test_different_subject(self):
        a = make_expr(subject="weather")
        b = make_expr(subject="temperature")
        assert a != b

    def test_inequality_with_non_expression(self):
        expr = make_expr()
        assert expr.__eq__("not an expression") is NotImplemented
