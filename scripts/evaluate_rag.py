"""
RAG evaluation harness.

Runs a fixed set of question/answer test cases against the live RAG
pipeline (real retrieval + real embeddings + real LLM calls) and reports
retrieval accuracy, answer correctness, and response time.

Run inside the app container so it shares the same environment
(DATABASE_URL, OLLAMA_BASE_URL) as the running application:

    docker compose exec app python scripts/evaluate_rag.py

Expects the document corpus to contain exactly these completed,
deduplicated documents (see project notes on corpus cleanup):
    - ml_document.txt
    - neural_networks.txt
    - python_basics.txt
    - coffee_brewing.txt
"""

import asyncio
import logging
import time
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.document import Document
from app.services.rag_service import RAGService

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("evaluate_rag")

TEST_CASES = [
    {
        "question": "What are the three main types of machine learning?",
        "expected_document": "ml_document.txt",
        "expected_keywords": ["supervised", "unsupervised", "reinforcement"],
    },
    {
        "question": "What is backpropagation used for?",
        "expected_document": "neural_networks.txt",
        "expected_keywords": ["weight", "bias", "adjust"],
    },
    {
        "question": "What is the difference between a list and a tuple in Python?",
        "expected_document": "python_basics.txt",
        "expected_keywords": ["mutable", "immutable"],
    },
    {
        "question": "What is the ideal water temperature for brewing coffee?",
        "expected_document": "coffee_brewing.txt",
        "expected_keywords": ["195", "205"],
    },
    {
        "question": "What are common activation functions in a neural network?",
        "expected_document": "neural_networks.txt",
        "expected_keywords": ["relu", "sigmoid", "tanh"],
    },
    {
        "question": "How does Python manage project dependencies?",
        "expected_document": "python_basics.txt",
        "expected_keywords": ["pip", "virtual environment"],
    },
    {
        "question": "What grind size should be used for a French press?",
        "expected_document": "coffee_brewing.txt",
        "expected_keywords": ["coarse"],
    },
    {
        "question": "What is deep learning?",
        "expected_document": "neural_networks.txt",
        "expected_keywords": ["deep", "hidden layers"],
    },
]


async def get_owner_id(db: AsyncSession) -> uuid.UUID | None:
    """Find the account that owns the known evaluation corpus (anchored on ml_document.txt)."""
    result = await db.execute(select(Document.owner_id).where(Document.filename == "ml_document.txt").limit(1))
    row = result.first()
    return row[0] if row else None


async def load_document_id_map(db: AsyncSession, owner_id: uuid.UUID) -> dict[str, uuid.UUID]:
    result = await db.execute(select(Document).where(Document.owner_id == owner_id))
    docs = result.scalars().all()
    return {doc.filename: doc.id for doc in docs}


async def run_evaluation() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        owner_id = await get_owner_id(db)
        if owner_id is None:
            logger.error("Could not find ml_document.txt for any user. Upload the evaluation corpus first.")
            await engine.dispose()
            return

        doc_map = await load_document_id_map(db, owner_id)
        missing = [c["expected_document"] for c in TEST_CASES if c["expected_document"] not in doc_map]
        if missing:
            logger.warning(f"Missing expected documents for this owner: {missing}")

        logger.info(f"Evaluating {len(TEST_CASES)} test cases | owner={owner_id} | corpus={list(doc_map.keys())}")
        logger.info("")

        rag_service = RAGService(db)
        results = []

        for i, case in enumerate(TEST_CASES, start=1):
            question = case["question"]
            expected_doc_id = doc_map.get(case["expected_document"])

            start = time.time()
            response = await rag_service.answer_question(question=question, owner_id=owner_id, top_k=3)
            elapsed_ms = int((time.time() - start) * 1000)

            retrieved_doc_ids = {source["document_id"] for source in response.sources}
            retrieval_hit = expected_doc_id is not None and str(expected_doc_id) in retrieved_doc_ids

            answer_lower = response.answer.lower()
            keyword_hits = [kw for kw in case["expected_keywords"] if kw.lower() in answer_lower]
            answer_pass = len(keyword_hits) >= max(1, len(case["expected_keywords"]) // 2)

            results.append(
                {
                    "retrieval_hit": retrieval_hit,
                    "answer_pass": answer_pass,
                    "elapsed_ms": elapsed_ms,
                }
            )

            status = "PASS" if (retrieval_hit and answer_pass) else "FAIL"
            logger.info(f"[{i}/{len(TEST_CASES)}] [{status}] {question}")
            logger.info(f"    Retrieval: {'hit' if retrieval_hit else 'MISS'} (expected {case['expected_document']})")
            logger.info(f"    Keywords found: {keyword_hits} / {case['expected_keywords']}")
            logger.info(f"    Time: {elapsed_ms}ms")
            logger.info(f"    Answer: {response.answer[:150]}")
            logger.info("")

    await engine.dispose()

    total = len(results)
    retrieval_passes = sum(1 for r in results if r["retrieval_hit"])
    answer_passes = sum(1 for r in results if r["answer_pass"])
    full_passes = sum(1 for r in results if r["retrieval_hit"] and r["answer_pass"])
    avg_time = sum(r["elapsed_ms"] for r in results) / total if total else 0

    logger.info("=" * 60)
    logger.info("EVALUATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total test cases:      {total}")
    logger.info(f"Retrieval accuracy:    {retrieval_passes}/{total} ({retrieval_passes / total * 100:.0f}%)")
    logger.info(f"Answer correctness:    {answer_passes}/{total} ({answer_passes / total * 100:.0f}%)")
    logger.info(f"Full pass (both):      {full_passes}/{total} ({full_passes / total * 100:.0f}%)")
    logger.info(f"Average response time: {avg_time:.0f}ms")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_evaluation())