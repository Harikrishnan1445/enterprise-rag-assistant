import logging
import time
import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk
from app.rag.embedder import embed_query
from app.rag.llm_client import generate_answer
from app.rag.prompt_builder import build_rag_prompt
from app.rag.retriever import retrieve_similar_chunks

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    answer: str
    sources: list[dict]
    chunks_retrieved: int


class RAGService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def answer_question(
        self,
        question: str,
        owner_id: uuid.UUID,
        top_k: int = 5,
        document_ids: list[uuid.UUID] | None = None,
    ) -> RAGResponse:
        start = time.time()
        logger.info(f"RAG query started | user={owner_id} | question='{question[:50]}'")

        query_embedding = embed_query(question)
        retrieval_start = time.time()

        chunks = await retrieve_similar_chunks(
            db=self.db,
            query_embedding=query_embedding,
            owner_id=owner_id,
            top_k=top_k,
            document_ids=document_ids,
        )
        retrieval_ms = int((time.time() - retrieval_start) * 1000)
        logger.info(f"Retrieval complete | chunks={len(chunks)} | time={retrieval_ms}ms")

        prompt = build_rag_prompt(question, chunks)
        llm_start = time.time()

        answer = await generate_answer(prompt)
        llm_ms = int((time.time() - llm_start) * 1000)
        total_ms = int((time.time() - start) * 1000)
        logger.info(f"RAG complete | retrieval={retrieval_ms}ms | llm={llm_ms}ms | total={total_ms}ms")

        sources = [
            {
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "chunk_index": chunk.chunk_index,
                "preview": chunk.content[:200],
            }
            for chunk in chunks
        ]

        return RAGResponse(answer=answer, sources=sources, chunks_retrieved=len(chunks))