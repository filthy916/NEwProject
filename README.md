# NEwProject — Machine Learning Symbolic Human-to-AI Translator

A lightweight, dependency-minimal Python library that converts natural-language
human utterances into structured **symbolic AI expressions** using a combination
of machine learning (TF-IDF + Logistic Regression) and a rule-based symbolic
encoder.

---

## How It Works

```
Human text
    │
    ▼
┌─────────────┐     normalise, expand contractions,
│ Preprocessor │◄── tokenise, remove stop words
└──────┬──────┘
       │ tokens + cleaned text
       ▼
┌──────────────────┐    TF-IDF n-gram vectorisation
│ IntentClassifier │◄── Logistic Regression over 8 intent classes
└──────┬───────────┘
       │ intent label + confidence
       ▼
┌─────────────────┐    entity extraction (TIME, LOCATION,
│ SymbolicEncoder │◄── QUANTITY, AGENT), subject resolution,
└──────┬──────────┘    formal predicate mapping
       │
       ▼
  SymbolicExpression
  predicate · intent · subject · arguments · confidence
```

### Intent taxonomy

| Intent | Symbolic predicate | Example utterance |
|---|---|---|
| `QUERY` | `∃?` | "Where is the nearest hospital?" |
| `COMMAND` | `DO` | "Turn on the lights" |
| `ASSERT` | `⊨` | "The sky is blue" |
| `CONDITIONAL` | `⟹` | "If it rains, I'll stay home" |
| `NEGATE` | `¬` | "There is no valid answer" |
| `COMPARE` | `≷` | "Compare Python versus JavaScript" |
| `DEFINE` | `≡` | "Define the word entropy" |
| `ENUMERATE` | `∈*` | "List all files in the directory" |

---

## Project structure

```
NEwProject/
├── main.py                      # CLI entry point
├── requirements.txt
├── src/
│   └── translator/
│       ├── __init__.py
│       ├── vocabulary.py        # Intent seeds, entity patterns, stop words
│       ├── preprocessor.py      # Text normalisation & tokenisation
│       ├── classifier.py        # TF-IDF + Logistic Regression intent classifier
│       ├── encoder.py           # Symbolic encoder (intent → SymbolicExpression)
│       ├── symbolic_expression.py  # Output data class
│       └── translator.py        # End-to-end HumanToAITranslator
└── tests/
    ├── test_preprocessor.py
    ├── test_symbolic_expression.py
    ├── test_classifier.py
    └── test_translator.py
```

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Quick start

### Python API

```python
from src.translator import HumanToAITranslator

translator = HumanToAITranslator()

expr = translator.translate("What is the weather today?")
print(expr)             # ∃?(what, time=today)
print(expr.intent)      # QUERY
print(expr.confidence)  # 0.8154
print(expr.to_json())
```

**Batch translation**

```python
results = translator.translate_batch([
    "Turn on the server",
    "List all database tables",
    "Compare Redis versus Memcached",
])
for expr in results:
    print(expr)
```

**Fine-tuning on your own examples**

```python
translator.train(
    texts=["reboot the machine", "restart the service"],
    labels=["COMMAND", "COMMAND"],
)
```

Custom examples are merged with the built-in seed corpus, so existing intent
knowledge is preserved.

### CLI

Translate a single sentence:

```bash
python main.py "Turn on the lights"
# DO(turn_lights)
```

Choose output format (`symbolic` / `dict` / `json`):

```bash
python main.py "Compare Redis versus Memcached" --format json
```

Batch-translate a file (one sentence per line):

```bash
python main.py --file sentences.txt --format json
```

Interactive REPL:

```bash
python main.py
# human> What is machine learning?
#    ai> ∃?(what)```

---

## Groq backend server

`server.py` is a Flask backend that proxies chat requests to the
[Groq API](https://console.groq.com).  **All Groq API calls happen
server-side** — the API key is never sent to the client or hardcoded in the
source.

### Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Create your `.env` file** (it is listed in `.gitignore` and never committed)

   ```bash
   cp .env.example .env
   ```

   Open `.env` and replace `your_groq_api_key_here` with your actual key from
   [console.groq.com](https://console.groq.com).

3. **Start the server**

   ```bash
   python server.py
   ```

### Deploying to Render

Render was trying to run `npm run start`, which fails because this repository is
a Python service. This repository now includes three deployment-friendly
entrypoints that all start the same Flask server:

- `package.json` so existing Render services that still run `npm run start`
  can successfully launch `python server.py`
- `render.yaml` for new Render blueprint-based web services
- `Procfile` for platforms that honor Procfile process definitions

If you create a new Render service from this repo, use the blueprint in
`render.yaml` or make sure the service is configured with:

```text
Build Command: pip install -r requirements.txt
Start Command: python server.py
```

Also set `GROQ_API_KEY` in the Render dashboard environment variables. Render
will provide `PORT`; `server.py` now reads it automatically and falls back to port `10000` when `PORT` is not set.

### API reference

#### `POST /api/chat`

| Field | Type | Required | Description |
|---|---|---|---|
| `message` | string | ✓ | The user's message |
| `model` | string | | Groq model name (default: `llama3-8b-8192`) |
| `system` | string | | Optional system prompt |

**Example request**

```bash
curl -X POST http://localhost:10000/api/chat \
     -H 'Content-Type: application/json' \
     -d '{"message": "What is the capital of France?"}'
```

**Example response**

```json
{
  "reply": "The capital of France is Paris.",
  "model": "llama3-8b-8192"
}
```

#### `GET /health`

Returns `{"status": "ok"}` — useful for uptime checks.

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | ✓ | — | Your Groq API key |
| `GROQ_MODEL` | | `llama3-8b-8192` | Default model |
| `FLASK_DEBUG` | | `0` | Set to `1` for dev mode |

---

## Running tests

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## Output format

Every `SymbolicExpression` exposes three serialisation methods:

| Method | Example output |
|---|---|
| `str(expr)` | `∃?(what, time=today)` |
| `expr.to_dict()` | plain Python dict |
| `expr.to_json()` | pretty-printed JSON |

The JSON representation:

```json
{
  "predicate": "∃?",
  "intent": "QUERY",
  "subject": "what",
  "arguments": { "time": "today" },
  "confidence": 0.8154,
  "raw_text": "What is the weather today?"
}
```

