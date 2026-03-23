"""Command-line interface for the Human-to-AI Translator.

Usage
-----
Translate a single sentence::

    python main.py "What is the capital of France?"

Interactive REPL mode (no arguments)::

    python main.py

Batch-translate from a file (one sentence per line)::

    python main.py --file sentences.txt

Output formats:  --format symbolic | dict | json  (default: symbolic)
"""

import argparse
import json
import sys
from pathlib import Path

# Allow running from the project root without installing the package
sys.path.insert(0, str(Path(__file__).parent))

from src.translator import HumanToAITranslator


def _format_result(expr, fmt: str) -> str:
    if fmt == "json":
        return expr.to_json()
    if fmt == "dict":
        return str(expr.to_dict())
    if fmt == "ai":
        return expr.to_ai_language()
    return str(expr)


def _repl(translator: HumanToAITranslator, fmt: str) -> None:
    print("Human-to-AI Translator — interactive mode")
    print("Type a sentence and press Enter.  Ctrl-C or Ctrl-D to quit.\n")
    while True:
        try:
            text = input("human> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not text:
            continue
        try:
            expr = translator.translate(text)
            print("   ai> ", _format_result(expr, fmt), "\n")
        except ValueError as exc:
            print(f"  err> {exc}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Machine-learning symbolic human-to-AI translator."
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Single sentence to translate (omit for interactive mode).",
    )
    parser.add_argument(
        "--file",
        metavar="PATH",
        help="Path to a text file with one sentence per line.",
    )
    parser.add_argument(
        "--format",
        choices=["symbolic", "dict", "json", "ai"],
        default="symbolic",
        dest="fmt",
        help="Output format (default: symbolic).",
    )
    args = parser.parse_args()

    translator = HumanToAITranslator()

    if args.file:
        path = Path(args.file)
        if not path.is_file():
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        results = translator.translate_batch(lines)
        output = []
        for line, expr in zip(lines, results):
            output.append({"input": line, "output": expr.to_dict()})
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    if args.text:
        expr = translator.translate(args.text)
        print(_format_result(expr, args.fmt))
        return

    _repl(translator, args.fmt)


if __name__ == "__main__":
    main()
