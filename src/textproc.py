import re
from typing import List, Dict, Any

# الحركات والتشكيل
TASHKEEL_REGEX = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
TATWEEL_REGEX = re.compile(r'\u0640')

# خريطة الأرقام المشرقية
ARABIC_DIGITS_MAP = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')

def remove_tashkeel(text: str) -> str:
    return TASHKEEL_REGEX.sub('', text)

def remove_tatweel(text: str) -> str:
    return TATWEEL_REGEX.sub('', text)

def normalize_arabic(text: str) -> str:
    """تطبيع كامل مخصص لمحرك البحث FTS5 والمطابقة الدقيقة"""
    if not text:
        return ""
    text = remove_tashkeel(text)
    text = remove_tatweel(text)
    # توحيد الألف
    text = re.sub(r'[إأآا]', 'ا', text)
    # توحيد الياء والألف المقصورة
    text = re.sub(r'[يى]', 'ي', text)
    # توحيد التاء المربوطة
    text = re.sub(r'ة', 'ه', text)
    # توحيد الأرقام
    text = text.translate(ARABIC_DIGITS_MAP)
    # تنظيف الفراغات المكررة
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_display(text: str) -> str:
    """تنظيف النص مع الحفاظ على الإملاء الأصلي للعرض والاستشهاد"""
    if not text:
        return ""
    text = remove_tatweel(text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def chunk_text(text: str, source: str, ref: str = "", chunk_size: int = 400, overlap: int = 50) -> List[Dict[str, Any]]:
    """تقسيم النص إلى Chunks مع الحفاظ على التداخل والمراجع"""
    words = text.split()
    if not words:
        return []
    
    chunks = []
    step = chunk_size - overlap
    if step <= 0:
        step = chunk_size
    
    total_words = len(words)
    chunk_index = 0
    for i in range(0, total_words, step):
        chunk_words = words[i:i + chunk_size]
        chunk_raw = " ".join(chunk_words)
        chunks.append({
            "chunk_id": f"{source}_{chunk_index}",
            "source": source,
            "ref": ref or f"Part {chunk_index + 1}",
            "text": chunk_raw,
            "text_norm": normalize_arabic(chunk_raw),
            "word_count": len(chunk_words)
        })
        chunk_index += 1
        if i + chunk_size >= total_words:
            break
            
    return chunks
