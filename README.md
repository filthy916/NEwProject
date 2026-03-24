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

## 1ONE Full-Stack Bridge

`server.py` now serves both:
- a stateless web frontend at `/` (single-turn bridge UI)
- backend APIs (`/api/bridge`, `/api/chat`, `/api/translate`)

All model API calls happen server-side.

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

   Or via npm:

   ```bash
   npm run start
   ```

### Deploying to Render

This repository includes a `package.json` launcher (`npm run start`) plus
`render.yaml` and `Procfile` entries for Python hosting.

If you create a new Render service from this repo, use the blueprint in
`render.yaml` or make sure the service is configured with:

```text
Build Command: pip install -r requirements.txt
Start Command: python server.py
```

Also set `GROQ_API_KEY` in the Render dashboard environment variables. Render
will provide `PORT`; `server.py` now reads it automatically.

### API reference

All `/api/*` endpoints require the bridge secret in one of these headers:

- `X-Auth-Secret: <BRIDGE_SECRET_916 or BRIDGE_SECRET>`
- `X-API-Key: <BRIDGE_SECRET_916 or BRIDGE_SECRET>` (compat)
- `Authorization: Bearer <BRIDGE_SECRET_916 or BRIDGE_SECRET>` (compat)

If no bridge secret env var is configured, auth is disabled and these headers are optional.

#### `POST /api/bridge`

Single-turn Human↔AI bridge endpoint.

| Field | Type | Required | Description |
|---|---|---|---|
| `direction` | string | | `human_to_ai` or `ai_to_human` |
| `text` | string | ✓ | Source payload |
| `provider` | string | | `groq` or `openai` (default `groq`) |
| `max_retries` | number | | 1..3 (default 3) |
| `format` | string | | `json` or `text` |

#### `POST /api/chat`

| Field | Type | Required | Description |
|---|---|---|---|
| `message` | string | ✓ | The user's message |
| `provider` | string | | `groq` or `openai` (default: `groq`) |
| `model` | string | | Provider model name (defaults from env) |
| `system` | string | | Optional system prompt |
| `resonate` | boolean | | Rewrite message to AI-oriented format (default: `true`) |
| `include_translation` | boolean | | Include translated intermediate payload |

**Example request**

```bash
curl -X POST http://localhost:5000/api/chat \
     -H 'Content-Type: application/json' \
     -H 'X-Auth-Secret: your_916_secret_here' \
     -d '{"message": "What is the capital of France?"}'
```

**Example response**

```json
{
  "reply": "The capital of France is Paris.",
  "model": "llama3-8b-8192"
}
```

#### `POST /api/translate`

Translate human text and return symbolic + substrate resonance.

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | string | ✓ | The source input text (alias: `message`) |
| `format` | string | | `symbolic`, `dict`, `json`, or `ai` (default: `ai`) |

Response includes:
- `symbolic` (structured symbolic expression)
- `substrate_truth` (resonance-layer intent extraction)
- `resonance_score` (0.0 to 1.0)

#### `GET /health`

Returns `{"status":"ok|degraded","groq_ready":...,"bridge_secret_protected":...}`.

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | | — | Your Groq API key |
| `OPENAI_API_KEY` | | — | Your OpenAI API key |
| `BRIDGE_SECRET_916` | | — | Optional shared secret to protect `/api/*` requests |
| `BRIDGE_SECRET` | | — | Optional alias for `BRIDGE_SECRET_916` |
| `GROQ_MODEL` | | `llama3-8b-8192` | Default model |
| `OPENAI_MODEL` | | `gpt-4o-mini` | Default OpenAI model |
| `FLASK_DEBUG` | | `0` | Set to `1` for dev mode |

Set either `BRIDGE_SECRET_916` or `BRIDGE_SECRET` only if you want protected API access.

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

