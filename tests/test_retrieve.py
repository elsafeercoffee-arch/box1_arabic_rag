from src.retrieve import hybrid_retrieve

def test_retrieve_labor_contract():
    results = hybrid_retrieve("فترة اختبار العامل", top_k=1)
    assert len(results) > 0
    assert "المادة 2" in results[0]["ref"]
    assert "ثلاثة أشهر" in results[0]["text"]

def test_retrieve_consumer_return():
    results = hybrid_retrieve("استرجاع السلعة خلال أربعة عشر يوما", top_k=1)
    assert len(results) > 0
    assert "المادة 11" in results[0]["ref"]
    assert "استبدال" in results[0]["text"]
