import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk


async def retrieve_similar_chunks(
    db: AsyncSession,
    query_embedding: list[float],
    owner_id: uuid.UUID,
    top_k: int = 5,
    document_ids: list[uuid.UUID] | None = None,
) -> list[DocumentChunk]:
    from app.models.document import Document

    stmt = (
        select(DocumentChunk)
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(Document.owner_id == owner_id)
        .where(DocumentChunk.embedding.isnot(None))
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )

    if document_ids:
        stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))

    result = await db.execute(stmt)
    return list(result.scalars().all())