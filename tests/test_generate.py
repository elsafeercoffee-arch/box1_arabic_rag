from src.generate import generate_answer, REFUSAL_PHRASE

def test_generate_refusal_on_empty_context():
    # التحقق من الرفض الحتمي عند غياب المستندات
    res = generate_answer("سؤال خارج المجال تماماً؟", chunks=[])
    assert res["answer"] == REFUSAL_PHRASE
    assert res["mode"] == "deterministic_refusal"
    assert len(res["citations"]) == 0

def test_generate_local_with_context():
    # التحقق من تضمين المرجع في الرد
    dummy_chunks = [{
        "source": "قانون_العمل",
        "ref": "المادة 2",
        "text": "فترة الاختبار لا تزيد عن ثلاثة أشهر."
    }]
    res = generate_answer("ما هي فترة الاختبار؟", chunks=dummy_chunks)
    assert "المادة 2" in res["answer"]
    assert "المادة 2" in res["citations"]
