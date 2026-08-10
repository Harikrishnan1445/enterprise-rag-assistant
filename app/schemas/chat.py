import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatRequest(BaseModel):
    question: str
    document_ids: list[uuid.UUID] | None = None
    top_k: int = 5


class SourceInfo(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    preview: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceInfo]
    chunks_retrieved: int


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    sources: list | None
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    created_at: datetime
    messages: list[MessageResponse] = []