from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)
VALID_KEY = "test-secret-key-12345"

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_ask_unauthorized():
    res = client.post("/ask", json={"question": "ما هي مدة فترة الاختبار؟"})
    assert res.status_code == 401

def test_ask_short_question():
    res = client.post(
        "/ask",
        headers={"X-API-Key": VALID_KEY},
        json={"question": "ما"}
    )
    assert res.status_code == 422

def test_ask_valid_with_pii_masking():
    res = client.post(
        "/ask",
        headers={"X-API-Key": VALID_KEY},
        json={"question": "ما هي فترة اختبار العامل؟ رقمي 01012345678"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "[REDACTED_PHONE]" in data["question"]
    assert "01012345678" not in data["question"]
    assert "المادة 2" in data["citations"]
