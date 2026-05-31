# CLAUDE.md — Grounded Reader (Project Brain)

## What This Project Is
A small high-assurance reading tool. The user gives it a SOURCE document and a
QUESTION. The app answers **only** from that source, shows the exact quote behind
every answer, and discards anything it cannot verify against the source. Built to
demonstrate trustworthy AI for settings where a wrong answer is expensive
(legal, clinical, financial, security).

## Stack
- Python + FastAPI (backend)
- Uvicorn (server)
- Anthropic Python SDK (model calls)
- Plain HTML / CSS / JS (front-end — framework-free on purpose)
- python-dotenv (config)

## Key Commands
```
pip install -r requirements.txt          # install dependencies
cp .env.example .env                      # then add your ANTHROPIC_API_KEY
uvicorn main:app --reload                 # run locally -> http://localhost:8000
python test_verify.py                     # run the verification-guard test (if present)
```

## The One Rule That Must Never Break (CRITICAL)
**Only verified claims are ever shown to the user.** A claim is "verified" when its
supporting quote genuinely appears in the source text (checked by `verify_quote` in
`main.py`). Never remove or weaken this step — it is the entire point of the project.

Two more hard rules:
- The Anthropic API key is read **server-side only** (from the environment / `.env`).
  Never send it to the browser, log it, or commit it.
- The model is never trusted blindly. The model reads; the code does the checking.

## File Structure — Sources of Truth
| File | Purpose |
|------|---------|
| `main.py` | FastAPI backend: `/analyze` endpoint, `verify_quote` guard, audit logging |
| `index.html` | Single-page front-end — paste source, ask, see verified answers |
| `sample.txt` | Sample document for testing |
| `requirements.txt` | Python dependencies |
| `Procfile` | Railway start command |
| `.env` | Secrets — `ANTHROPIC_API_KEY`, `MODEL` (gitignored, never committed) |
| `.env.example` | Template for `.env` |
| `.claude/agents/` | Claude Code subagents (see below) |

## Agents (.claude/agents/)
| Agent | Use it when |
|-------|-------------|
| `debugger` | Something fails — server won't start, model/JSON errors, guard acting up |
| `code-reviewer` | After changing any code, before committing |
| `feature-builder` | Adding a new endpoint, check, or UI feature |

## Conventions
- Python: standard library + the listed dependencies only; small functions, plain-English comments.
- Any new logic that affects what the user sees ships with a small test.
- Front-end stays framework-free so it's trivial to deploy; always escape text inserted into the DOM.

## Deployment
- Railway: deploy from the GitHub repo; the `Procfile` starts the app. Set
  `ANTHROPIC_API_KEY` (and optionally `MODEL`) as Railway variables.
- Python version is auto-detected; add a `.python-version` only if needed (verify on Railway).

## Accuracy Note
SDK usage follows the official Anthropic Python SDK docs, but model names change.
Confirm the current model list at https://docs.claude.com before pinning one.
