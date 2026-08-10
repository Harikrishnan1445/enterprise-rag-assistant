import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk
from app.rag.embedder import embed_query
from app.rag.llm_client import generate_answer
from app.rag.prompt_builder import build_rag_prompt
from app.rag.retriever import retrieve_similar_chunks


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
        query_embedding = embed_query(question)

        chunks = await retrieve_similar_chunks(
            db=self.db,
            query_embedding=query_embedding,
            owner_id=owner_id,
            top_k=top_k,
            document_ids=document_ids,
        )

        prompt = build_rag_prompt(question, chunks)
        answer = await generate_answer(prompt)

        sources = [
            {
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "chunk_index": chunk.chunk_index,
                "preview": chunk.content[:200],
            }
            for chunk in chunks
        ]

        return RAGResponse(
            answer=answer,
            sources=sources,
            chunks_retrieved=len(chunks),
        )