# BOX 1: Arabic Hybrid RAG Engine

A production-grade, low-resource Arabic Retrieval-Augmented Generation (RAG) engine built entirely on Samsung Galaxy S8+ (Termux) with zero paid cloud services.

## Architecture
- **Lexical Search**: SQLite FTS5 with BM25 scoring and custom Arabic normalization (Tashkeel, Tatweel, Alef, Yaa, and Eastern Arabic numerals unification).
- **Vector Search**: Cosine Similarity via NumPy (float32 embeddings).
- **Hybrid Fusion**: Reciprocal Rank Fusion (RRF) with k=60.
- **Security & Guardrails**:
  - API Key Authentication (`X-API-Key`) with strict 401 enforcement.
  - Rate Limiting via `slowapi` (20 req/min).
  - PII Masking (Egyptian/Gulf Phone numbers, Emails).
  - Regex-based Two-Tier Prompt Injection Detection.
  - Deterministic Refusal on empty or out-of-domain context.

## Benchmark & Evaluation (Samsung Galaxy S8+)
- **Average Latency**: 5.22 ms
- **Recall@3**: 80.0%
- **Citation Accuracy**: 70.0%
- **False Refusal Rate**: 0.0%
- **Test Coverage**: 15 passed pytest unit & security tests.

## API Endpoints
- `GET /health`: Healthcheck.
- `POST /ask`: Submit question (3-500 chars, protected by API Key).
