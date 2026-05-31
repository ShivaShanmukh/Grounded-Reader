---
name: debugger
description: Diagnoses Grounded Reader failures — server won't start, model call errors, JSON parse errors, or the verification guard behaving unexpectedly
tools: Read, Bash, Grep
model: sonnet
---

When debugging a failure:
1. Confirm the environment: the `.venv` is active, `pip install -r requirements.txt` has run, and `.env` contains `ANTHROPIC_API_KEY` (check that it is set — never print its value).
2. Try to start the server with `uvicorn main:app --reload` and capture the full traceback.
3. Identify which layer failed: FastAPI startup, the model call inside `/analyze`, the JSON parsing (`parse_model_json`), the verification guard (`verify_quote`), or the front-end fetch.
4. For model or parse errors, log the raw model output once to the console (never commit it) to see exactly what came back.
5. Propose the smallest fix. Do NOT weaken or bypass the verification step to "make it pass" — a guard that rejects something is a real signal, not a bug to silence.
