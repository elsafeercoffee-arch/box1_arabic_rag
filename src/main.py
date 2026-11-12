import os
from fastapi import FastAPI, Depends, Request
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.security import verify_api_key, mask_pii, is_prompt_injection
from src.retrieve import hybrid_retrieve
from src.generate import generate_answer, REFUSAL_PHRASE

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Arabic RAG API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)

@app.get("/health")
def health():
    return {"status": "ok", "service": "Arabic RAG"}

@app.post("/ask")
@limiter.limit("20/minute")
def ask(request: Request, body: AskRequest, api_key: str = Depends(verify_api_key)):
    masked_q = mask_pii(body.question)

    # فحص أمني: حظر Prompt Injection فوراً
    if is_prompt_injection(masked_q):
        return {
            "question": masked_q,
            "answer": REFUSAL_PHRASE,
            "citations": [],
            "mode": "blocked_injection"
        }

    chunks = hybrid_retrieve(masked_q, top_k=3)
    gen_result = generate_answer(masked_q, chunks)
    return {
        "question": masked_q,
        "answer": gen_result["answer"],
        "citations": gen_result["citations"],
        "mode": gen_result["mode"]
    }
