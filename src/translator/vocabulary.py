"""Symbolic vocabulary and ontology for the human-to-AI translator.

Maps human language patterns to formal symbolic tokens and defines the
ontology of intents, entities, and relations used in symbolic expressions.
"""

# ---------------------------------------------------------------------------
# Intent taxonomy
# ---------------------------------------------------------------------------

INTENT_LABELS = [
    "QUERY",        # asking for information
    "COMMAND",      # requesting an action
    "ASSERT",       # stating a fact
    "CONDITIONAL",  # if/then reasoning
    "NEGATE",       # negating a statement
    "COMPARE",      # comparing two or more things
    "DEFINE",       # asking for a definition
    "ENUMERATE",    # listing items
]

# ---------------------------------------------------------------------------
# Keyword → intent seed mapping used to build the training corpus
# ---------------------------------------------------------------------------

INTENT_SEEDS: dict[str, list[str]] = {
    "QUERY": [
        "what is", "what are", "who is", "where is", "when did",
        "how does", "why does", "tell me about", "explain",
        "describe", "what was", "how many", "which one",
        "can you tell", "do you know", "where can i find",
        "what is the weather", "what is the temperature",
        "what is the capital", "what is the population",
        "who invented", "when was", "how old is",
        "how far is", "what time is", "which country",
    ],
    "COMMAND": [
        "turn on", "turn off", "open", "close", "run", "start",
        "stop", "execute", "delete", "create", "add", "remove",
        "set", "enable", "disable", "show me", "find", "search for",
        "compute", "calculate", "convert",
    ],
    "ASSERT": [
        "the sky is", "it is", "i believe", "i think", "i know",
        "this is", "that is", "there is", "there are", "it was",
        "they are", "the fact is", "it seems", "appears to be",
    ],
    "CONDITIONAL": [
        "if", "unless", "provided that", "given that", "assuming",
        "in case", "whenever", "should", "were", "had",
    ],
    "NEGATE": [
        "is not", "are not", "was not", "cannot", "do not",
        "does not", "never", "no", "nothing", "nobody",
        "neither", "nor", "deny", "refute",
    ],
    "COMPARE": [
        "compare", "difference between", "versus", "vs",
        "better than", "worse than", "similar to", "unlike",
        "same as", "as good as", "more than", "less than",
        "which is bigger", "which is faster",
    ],
    "DEFINE": [
        "define", "what does mean", "what is the meaning of",
        "what is the definition of", "explain the term",
        "meaning of", "what do you mean by", "define the word",
        "what is the concept of", "what does the term mean",
    ],
    "ENUMERATE": [
        "list", "name all", "give me all", "enumerate",
        "show all", "what are the types", "what kinds",
        "categories of", "examples of",
    ],
}

# ---------------------------------------------------------------------------
# Symbolic predicates for each intent
# ---------------------------------------------------------------------------

INTENT_TO_PREDICATE: dict[str, str] = {
    "QUERY":       "∃?",
    "COMMAND":     "DO",
    "ASSERT":      "⊨",
    "CONDITIONAL": "⟹",
    "NEGATE":      "¬",
    "COMPARE":     "≷",
    "DEFINE":      "≡",
    "ENUMERATE":   "∈*",
}

# ---------------------------------------------------------------------------
# Entity type patterns
# ---------------------------------------------------------------------------

ENTITY_PATTERNS: dict[str, list[str]] = {
    "TIME": [
        "today", "yesterday", "tomorrow", "now", "soon", "later",
        "morning", "evening", "night", "year", "month", "week",
        "monday", "tuesday", "wednesday", "thursday", "friday",
        "saturday", "sunday", "january", "february", "march",
        "april", "may", "june", "july", "august", "september",
        "october", "november", "december",
    ],
    "QUANTITY": [
        "one", "two", "three", "four", "five", "six", "seven",
        "eight", "nine", "ten", "hundred", "thousand", "million",
        "all", "none", "many", "few", "several", "every",
    ],
    "LOCATION": [
        "here", "there", "home", "office", "city", "country",
        "world", "north", "south", "east", "west", "above",
        "below", "inside", "outside",
    ],
    "AGENT": [
        "i", "me", "we", "us", "you", "he", "she", "they",
        "it", "user", "system", "model", "ai", "human",
    ],
}

# ---------------------------------------------------------------------------
# Stop words to remove during preprocessing
# ---------------------------------------------------------------------------

STOP_WORDS: set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at",
    "to", "for", "of", "with", "by", "from", "as", "into",
    "through", "during", "this", "that", "these", "those",
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can",
    "very", "just", "also", "so", "yet", "still", "both",
    "each", "more", "most", "other", "some", "such", "no",
    "its", "our", "your", "their", "my", "his", "her",
}
