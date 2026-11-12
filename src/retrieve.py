import os
import sqlite3
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from src.textproc import normalize_arabic

DB_PATH = os.path.join("data", "rag.db")

AR_STOPWORDS = {
    "ما", "هو", "هي", "ماذا", "هل", "كم", "من", "في", "على", "الى", "إلى", "عن",
    "مع", "هذا", "هذه", "ذلك", "تلك", "كان", "يكون", "التي", "الذي", "الذين", "او", "أو"
}

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def rrf(rank_lists: List[List[str]], k: int = 60) -> List[Tuple[str, float]]:
    scores = {}
    for r_list in rank_lists:
        for rank, cid in enumerate(r_list):
            scores[cid] = scores.get(cid, 0.0) + (1.0 / (k + rank + 1))
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

def search_bm25(query: str, limit: int = 10, db_path: str = DB_PATH) -> List[str]:
    norm_q = normalize_arabic(query)
    tokens = [w for w in norm_q.split() if w and w not in AR_STOPWORDS and len(w) > 1]
    if not tokens:
        tokens = [w for w in norm_q.split() if w]
    if not tokens:
        return []

    match_query = " OR ".join(f'"{t}"' for t in tokens)
    conn = get_connection(db_path)
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT chunk_id, bm25(fts) as score
            FROM fts
            WHERE fts MATCH ?
            ORDER BY score ASC
            LIMIT ?
        """, (match_query, limit))
        rows = cur.fetchall()
        return [row["chunk_id"] for row in rows]
    except Exception:
        return []
    finally:
        conn.close()

def search_vector(query_emb: Optional[np.ndarray], limit: int = 10, db_path: str = DB_PATH) -> List[str]:
    if query_emb is None:
        return []
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, emb FROM chunks WHERE emb IS NOT NULL")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return []

    q_norm = np.linalg.norm(query_emb)
    if q_norm == 0:
        return []
    q_vec = query_emb / q_norm

    scores = []
    for row in rows:
        cid = row["id"]
        blob = row["emb"]
        emb = np.frombuffer(blob, dtype=np.float32)
        emb_norm = np.linalg.norm(emb)
        if emb_norm > 0:
            sim = float(np.dot(q_vec, emb / emb_norm))
            scores.append((cid, sim))

    scores.sort(key=lambda x: x[1], reverse=True)
    return [cid for cid, _ in scores[:limit]]

def hybrid_retrieve(query: str, query_emb: Optional[np.ndarray] = None, top_k: int = 4, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    bm25_ids = search_bm25(query, limit=top_k * 2, db_path=db_path)
    vector_ids = search_vector(query_emb, limit=top_k * 2, db_path=db_path)

    active_lists = []
    if bm25_ids:
        active_lists.append(bm25_ids)
    if vector_ids:
        active_lists.append(vector_ids)

    if not active_lists:
        return []

    ranked = rrf(active_lists, k=60)
    final_ids = [cid for cid, _ in ranked[:top_k]]

    conn = get_connection(db_path)
    cur = conn.cursor()
    placeholders = ",".join("?" for _ in final_ids)
    cur.execute(f"SELECT id, source, ref, text FROM chunks WHERE id IN ({placeholders})", final_ids)
    rows_dict = {row["id"]: dict(row) for row in cur.fetchall()}
    conn.close()

    results = []
    for cid, score in ranked[:top_k]:
        if cid in rows_dict:
            item = rows_dict[cid]
            item["score"] = round(score, 4)
            results.append(item)
    return results
