import re
import os
from typing import Optional
from fastapi import Header, HTTPException, status

DEFAULT_TEST_KEY = "test-secret-key-12345"

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_REGEX = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b01[0125]\d{8}\b')

INJECTION_PATTERNS = [
    re.compile(r'تجاهل\s+(كل\s+)?(الاوامر|الأوامر|التعليمات)', re.IGNORECASE),
    re.compile(r'انس\s+ما\s+سبق', re.IGNORECASE),
    re.compile(r'اكشف\s+(عن\s+)?(التعليمات|النظام|system\s+prompt)', re.IGNORECASE),
    re.compile(r'ignore\s+(all\s+)?previous\s+instructions', re.IGNORECASE),
    re.compile(r'system\s+prompt', re.IGNORECASE),
]

def mask_pii(text: str) -> str:
    if not text:
        return ""
    text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
    return text

def is_prompt_injection(text: str) -> bool:
    """اكتشاف محاولات كسر التعليمات وحقن الأوامر"""
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False

def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    expected_key = os.getenv("APP_API_KEY", DEFAULT_TEST_KEY)
    if not x_api_key or x_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
    return x_api_key
