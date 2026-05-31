# Grounded Reader

A small reading tool for high-assurance settings. You give it a document and a
question. It answers **only** from that document, shows the exact line behind
every answer, and **discards anything it can't prove is really in the text.**

Most AI tools sound confident even when they're wrong. This one would rather say
*"not found"* than guess — which is exactly what you want in places where a wrong
answer is expensive (legal, clinical, financial, security).

## The one idea worth understanding

The AI does the reading. **The code does the checking.**

1. The AI is told: answer only from the source, and give the exact quote behind
   every claim.
2. For every quote it returns, the backend checks the quote **actually appears in
   the source**. If it doesn't, that claim is thrown away before the user ever
   sees it.
3. Every run is logged (what was returned, what was kept, what was discarded).

That verification step is the whole point. It turns "trust me" into "here's the
proof." A model can't fabricate a citation, because a fabricated quote won't be
found in the source and gets dropped.

## How it's built

- `main.py` — the backend (Python / FastAPI). Calls the model, then verifies and
  logs.
- `index.html` — the front-end. One screen: paste, ask, see verified answers.
- `requirements.txt`, `Procfile`, `.env.example` — setup.

## Run it locally

1. Install: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and add your Anthropic API key.
3. Start: `uvicorn main:app --reload`
4. Open `http://localhost:8000`

## Deploy to Railway

1. Push this folder to a GitHub repo.
2. In Railway: New Project → Deploy from GitHub repo.
3. Add `ANTHROPIC_API_KEY` as a variable (and optionally `MODEL`).
4. Railway uses the `Procfile` to start it. Done — you get a live URL.

The API key lives only on the server, never in the browser. (That's a deliberate
high-assurance choice — secrets never reach the client.)

## A note on accuracy

The Anthropic SDK calls here follow the official Python SDK docs, but model names
and API details change. Confirm the current model list at https://docs.claude.com
before relying on a specific one. The default model is set in `.env`.
