import json
import time
import os
from typing import Dict, Any
from src.retrieve import hybrid_retrieve
from src.generate import generate_answer, REFUSAL_PHRASE
from src.security import is_prompt_injection

GOLDEN_FILE = os.path.join("data", "golden.jsonl")
REPORT_FILE = os.path.join("docs", "eval_report.md")

def evaluate_system():
    if not os.path.exists(GOLDEN_FILE):
        print(f"[!] Golden file missing: {GOLDEN_FILE}")
        return

    with open(GOLDEN_FILE, "r", encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]

    total = len(cases)
    answerable_cases = [c for c in cases if c["is_answerable"]]
    unanswerable_cases = [c for c in cases if not c["is_answerable"]]

    recall_hits = 0
    citation_hits = 0
    false_refusals = 0
    correct_refusals = 0
    latencies = []

    for c in cases:
        q = c["question"]
        t0 = time.perf_counter()

        if is_prompt_injection(q):
            res = {"answer": REFUSAL_PHRASE, "citations": [], "mode": "blocked_injection"}
            chunks = []
        else:
            chunks = hybrid_retrieve(q, top_k=3)
            res = generate_answer(q, chunks)

        dt = (time.perf_counter() - t0) * 1000
        latencies.append(dt)

        if c["is_answerable"]:
            retrieved_refs = [chk.get("ref", "") for chk in chunks]
            exp = c["expected_ref"]
            if any(exp in r for r in retrieved_refs):
                recall_hits += 1

            if any(exp in cit for cit in res.get("citations", [])):
                citation_hits += 1

            if REFUSAL_PHRASE in res.get("answer", ""):
                false_refusals += 1
        else:
            if REFUSAL_PHRASE in res.get("answer", "") or len(res.get("citations", [])) == 0:
                correct_refusals += 1

    ans_count = len(answerable_cases)
    unans_count = len(unanswerable_cases)

    recall_rate = (recall_hits / ans_count) * 100 if ans_count else 0
    citation_rate = (citation_hits / ans_count) * 100 if ans_count else 0
    false_refusal_rate = (false_refusals / ans_count) * 100 if ans_count else 0
    correct_refusal_rate = (correct_refusals / unans_count) * 100 if unans_count else 0
    avg_latency = sum(latencies) / total if total else 0

    report = f"""# Arabic RAG Evaluation Report
Generated: Baseline Local Evaluation

## Key Metrics
| Metric | Value |
|---|---|
| Total Questions | {total} |
| Answerable Cases | {ans_count} |
| Unanswerable Cases | {unans_count} |
| **Recall@3** | **{recall_rate:.1f}%** |
| **Citation Accuracy** | **{citation_rate:.1f}%** |
| **Correct Refusal Rate** | **{correct_refusal_rate:.1f}%** |
| **False Refusal Rate** | **{false_refusal_rate:.1f}%** |
| **Average Latency** | **{avg_latency:.2f} ms** |

## Summary
- Fast FTS5 + RRF Hybrid retrieval on SQLite
- Deterministic refusal for out-of-domain and prompt injection attacks
- Zero cloud costs and runs locally on Samsung Galaxy S8+
"""

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report.strip())

    print("=== EVALUATION FINISHED ===")
    print(f"Recall@3: {recall_rate:.1f}%")
    print(f"Citation Accuracy: {citation_rate:.1f}%")
    print(f"Correct Refusal Rate: {correct_refusal_rate:.1f}%")
    print(f"False Refusal Rate: {false_refusal_rate:.1f}%")
    print(f"Average Latency: {avg_latency:.2f} ms")
    print(f"Report written to: {REPORT_FILE}")

if __name__ == "__main__":
    evaluate_system()
