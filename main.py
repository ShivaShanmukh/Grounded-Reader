"""
Grounded Reader — a small high-assurance reading tool.

What it does:
  1. Takes a SOURCE document + a QUESTION from the user.
  2. Asks the AI to answer ONLY from the source, and to hand back the exact
     word-for-word quote behind every claim.
  3. VERIFIES each quote really exists in the source. Anything it can't verify
     is discarded — this is the anti-hallucination guard.
  4. Logs every step so the whole run can be audited later.

The AI does the reading. The Python code does the checking. Nothing the user
sees is unverified.
"""

import os
import re
import json
import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("grounded-reader")

# NOTE: SDK usage (Anthropic() + client.messages.create) was checked against the
# official Anthropic Python SDK docs. Model names change over time — confirm the
# current list at https://docs.claude.com before relying on a specific one.
MODEL = os.environ.get("MODEL", "claude-sonnet-4-6")

client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment / .env

app = FastAPI(title="Grounded Reader")


class AnalyzeRequest(BaseModel):
    source: str
    question: str


SYSTEM_PROMPT = """You are a careful reading assistant for high-assurance settings.
You answer ONLY using the SOURCE text provided. You never use outside knowledge.

Return your findings as JSON in exactly this shape:
{
  "findings": [
    {"claim": "<one factual statement that answers the question>",
     "quote": "<the exact, word-for-word phrase from the SOURCE that supports it>"}
  ],
  "answer_found": true
}

Rules:
- Every "quote" MUST be copied verbatim from the SOURCE. Never paraphrase a quote.
- If the SOURCE does not contain the answer, return {"findings": [], "answer_found": false}.
- Do not guess and do not add anything that is not in the SOURCE.
- Return ONLY the JSON object — no prose, no markdown, no code fences.
"""


def _normalize(text: str) -> str:
    # Collapse all whitespace and lowercase, so a quote still matches even if the
    # model copied it with slightly different spacing or capitalisation.
    return re.sub(r"\s+", " ", text).strip().lower()


def verify_quote(source: str, quote: str) -> bool:
    """The guard: a quote only counts if it genuinely appears in the source."""
    if not quote:
        return False
    return _normalize(quote) in _normalize(source)


def parse_model_json(raw: str) -> dict:
    # Be forgiving if the model wraps JSON in code fences despite instructions.
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return json.loads(cleaned)


@app.get("/")
def home():
    return FileResponse("index.html")


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    request_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    log.info("request_id=%s step=received source_chars=%d", request_id, len(req.source))

    user_content = f'SOURCE:\n"""\n{req.source}\n"""\n\nQUESTION: {req.question}'

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
    except Exception as e:  # noqa: BLE001 - surface a clean error to the UI
        log.error("request_id=%s step=model_error error=%s", request_id, e)
        return JSONResponse(
            status_code=502,
            content={"error": "Model call failed. Check your API key and model name."},
        )

    raw = "".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    )
    log.info("request_id=%s step=model_returned chars=%d", request_id, len(raw))

    try:
        data = parse_model_json(raw)
    except Exception:  # noqa: BLE001
        log.error("request_id=%s step=parse_error", request_id)
        return JSONResponse(
            status_code=500, content={"error": "Could not read the model's response."}
        )

    findings = data.get("findings", []) or []
    verified, rejected = [], []
    for f in findings:
        claim = f.get("claim", "")
        quote = f.get("quote", "")
        (verified if verify_quote(req.source, quote) else rejected).append(
            {"claim": claim, "quote": quote}
        )

    log.info(
        "request_id=%s step=verified ok=%d rejected=%d answer_found=%s",
        request_id, len(verified), len(rejected), data.get("answer_found"),
    )

    return {
        "request_id": request_id,
        # Only call it "found" if the model said so AND at least one claim survived verification.
        "answer_found": bool(data.get("answer_found")) and len(verified) > 0,
        "verified": verified,
        "rejected": rejected,
        "audit": {
            "model": MODEL,
            "claims_returned": len(findings),
            "claims_verified": len(verified),
            "claims_rejected": len(rejected),
        },
    }
