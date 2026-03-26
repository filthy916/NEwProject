"""The Machine pressure test suite.

Runs 12 adversarial/edge-case prompts through a Groq chat model and prints
structured outputs for rapid prompt stress testing.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Sequence

from groq import Groq

SYSTEM_PROMPT = """
You are a Cognitive Query Architect. Your sole function is to receive raw,
unstructured, sloppy, emotional, or broken human input - and reconstruct
it as a precise, intellectually rigorous analytical inquiry.

You draw from these disciplines to reframe the input:
- Epistemology (nature of knowledge, justified belief, inquiry structure)
- Systems Theory (feedback loops, emergence, interdependence)
- Semiotics (sign systems, what words point to vs. what they ARE)
- Phenomenology (what is the lived experience behind the question?)
- Causal Inference (correlation vs. causation, confounders, mechanisms)
- Primitive Root Linguistics (strip words to their proto-language roots -
  find the OLDEST, most elemental meaning beneath the modern usage)
- Socratic Method (reframe as a falsifiable, testable, or explorable proposition)

HARD CONSTRAINTS:
1. Never repeat the user's original wording
2. Never ask the question directly - describe its analytical skeleton
3. Use domain-specific technical vocabulary (epistemological, ontological,
   mechanistic, phenomenological, empirical, causal, systemic)
4. Strip the question to its PRIMITIVE CORE - what is the human actually
   probing beneath the surface-level words?
5. Output MUST follow this exact 4-part structure:

   [ROOT INTENT]
   What elemental drive or primitive inquiry underlies this input?
   (use proto-language or root-word etymology if helpful)

   [ANALYTICAL REFRAME]
   The question, rebuilt as a precise academic/scientific inquiry.
   1-3 sentences. Zero colloquialisms.

   [DOMAIN AXIS]
   Which field(s) of study govern this inquiry? List 2-4 domains.

   [EPISTEMIC CHALLENGE]
   What makes this question hard to answer? What assumptions must be
   interrogated before valid investigation can begin?

Output ONLY this 4-part structure. Nothing else.
""".strip()

TEST_INPUTS = [
    "bro why my homie always switching up on me like that",
    "consciousness",
    "i just dont understand why nothing ever works out for me man like wtf",
    "yo how do wifi passwords get cracked",
    "if i cant trust my own thoughts how do i know what to believe",
    "whats the point of any of this",
    "the government is lying to everyone",
    "why do i keep asking the same questions",
    "i dont know like... just stuff ya know",
    "sql injection like when u put weird stuff in forms and it breaks",
    "does free will exist or are we just programmed",
    "im so tired of everything",
]


def build_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        print(
            "[ERROR] GROQ_API_KEY is not set. Add it to your environment before running this script.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return Groq(api_key=api_key)


def run_test(
    client: Groq,
    index: int,
    raw_input: str,
    model: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
) -> None:
    print(f"\n{'=' * 60}")
    print(f'  TEST {index:02d} | INPUT: "{raw_input}"')
    print(f"{'=' * 60}\n")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": raw_input},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        result = (response.choices[0].message.content or "").strip()
        print(result or "[EMPTY OUTPUT]")
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Test {index:02d} failed: {exc}")

    print()


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run The Machine pressure test suite")
    parser.add_argument("--model", default="llama-3.3-70b-versatile")
    parser.add_argument("--temperature", type=float, default=0.65)
    parser.add_argument("--top-p", type=float, default=0.92, dest="top_p")
    parser.add_argument("--max-tokens", type=int, default=768, dest="max_tokens")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    client = build_client()

    print("\n+==========================================================+")
    print("|       THE MACHINE - PRESSURE TEST SUITE (12 Cases)       |")
    print("|       sloppy / paradox / slang / edge / recursive        |")
    print("+==========================================================+")
    print(
        f"\nModel={args.model} Temperature={args.temperature} TopP={args.top_p} MaxTokens={args.max_tokens}"
    )

    for i, test in enumerate(TEST_INPUTS, start=1):
        run_test(
            client=client,
            index=i,
            raw_input=test,
            model=args.model,
            temperature=args.temperature,
            top_p=args.top_p,
            max_tokens=args.max_tokens,
        )

    print(f"\n{'=' * 60}")
    print("  ALL TESTS COMPLETE")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
