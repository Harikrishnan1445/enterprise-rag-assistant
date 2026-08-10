from app.models.document_chunk import DocumentChunk


def build_rag_prompt(question: str, chunks: list[DocumentChunk]) -> str:
    if not chunks:
        return f"""You are a helpful assistant. Answer the following question based on your general knowledge.

Question: {question}

Answer:"""

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(f"[Source {i}]\n{chunk.content}")

    context = "\n\n".join(context_parts)

    return f"""You are a helpful assistant that answers questions based ONLY on the provided context.
If the answer cannot be found in the context, say "I cannot find this information in the provided documents."
Do not use any outside knowledge.

Context:
{context}

Question: {question}

Answer:"""