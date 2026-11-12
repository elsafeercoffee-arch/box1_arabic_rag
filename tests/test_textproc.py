from src.textproc import normalize_arabic, clean_display, chunk_text

def test_normalize_arabic():
    raw = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ... قَانُونُ العَمَلِ رَقْم ١٢ لِسَنَةِ ٢٠٠٣"
    norm = normalize_arabic(raw)
    assert "بسم" in norm
    assert "الله" in norm
    assert "قانون" in norm
    assert "العمل" in norm
    assert "12" in norm
    assert "2003" in norm

def test_alef_and_teh_normalization():
    assert normalize_arabic("إدارة") == normalize_arabic("اداره")
    assert normalize_arabic("مستشفى") == normalize_arabic("مستشفي")

def test_chunking():
    sample_text = " ".join([f"كلمة_{i}" for i in range(100)])
    chunks = chunk_text(sample_text, source="law_doc", chunk_size=30, overlap=5)
    assert len(chunks) > 1
    assert chunks[0]["source"] == "law_doc"
    assert "text_norm" in chunks[0]
