import os
import sqlite3
import numpy as np
from typing import List, Optional
from src.textproc import normalize_arabic, chunk_text

DB_PATH = os.path.join("data", "rag.db")

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DB_PATH):
    """تهيئة جداول قاعدة البيانات ومحرك FTS5"""
    conn = get_connection(db_path)
    cur = conn.cursor()
    
    # 1. جدول المقاطع الأساسي
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id TEXT PRIMARY KEY,
        source TEXT NOT NULL,
        ref TEXT,
        text TEXT NOT NULL,
        text_norm TEXT NOT NULL,
        emb BLOB
    )
    """)
    
    # 2. جدول FTS5 للبحث النصي الكامل
    cur.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(
        text_norm,
        chunk_id UNINDEXED
    )
    """)
    conn.commit()
    conn.close()

def ingest_text_file(filepath: str, source_name: str, db_path: str = DB_PATH) -> int:
    """قراءة ملف، تقسيمه، وإدخاله في قاعدة البيانات مع دعم الاستئناف"""
    if not os.path.exists(filepath):
        print(f"[!] File not found: {filepath}")
        return 0
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # تقسيم المستند إلى فقرات بحسب المواد
    paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
    inserted = 0
    
    conn = get_connection(db_path)
    cur = conn.cursor()
    
    for idx, p in enumerate(paragraphs):
        ref = f"فقرة {idx+1}"
        if p.startswith("المادة"):
            ref = p.split(":")[0].strip()
            
        chunk_id = f"{source_name}_{idx+1}"
        text_norm = normalize_arabic(p)
        
        # فحص هل المقطع موجود مسبقاً (دعم الاستئناف)
        cur.execute("SELECT id FROM chunks WHERE id = ?", (chunk_id,))
        if cur.fetchone():
            continue
            
        # حفظ المقطع
        cur.execute("""
        INSERT INTO chunks (id, source, ref, text, text_norm, emb)
        VALUES (?, ?, ?, ?, ?, NULL)
        """, (chunk_id, source_name, ref, p, text_norm))
        
        # فهرسة المقطع في FTS5
        cur.execute("""
        INSERT INTO fts (text_norm, chunk_id)
        VALUES (?, ?)
        """, (text_norm, chunk_id))
        
        inserted += 1
        
    conn.commit()
    conn.close()
    return inserted

def verify_counts(db_path: str = DB_PATH):
    """التحقق من عدد السجلات في كل من الجدولين"""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM chunks")
    c_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM fts")
    f_count = cur.fetchone()[0]
    conn.close()
    print(f"[*] Total Chunks in DB: {c_count}")
    print(f"[*] Total Records in FTS: {f_count}")
    return c_count, f_count

if __name__ == "__main__":
    init_db()
    c1 = ingest_text_file("data/labor_law_sample.txt", "قانون_العمل")
    c2 = ingest_text_file("data/consumer_law_sample.txt", "حماية_المستهلك")
    print(f"[+] Ingested {c1} from Labor Law, {c2} from Consumer Law.")
    verify_counts()
