
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.db.session import get_db
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ConversationResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    rag_service = RAGService(db)
    result = await rag_service.answer_question(
        question=request.question,
        owner_id=current_user.id,
        top_k=request.top_k,
        document_ids=request.document_ids,
    )

    conversation = Conversation(owner_id=current_user.id, title=request.question[:100])
    db.add(conversation)
    await db.flush()

    user_msg = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER.value,
        content=request.question,
    )
    db.add(user_msg)

    assistant_msg = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT.value,
        content=result.answer,
        sources=result.sources,
    )
    db.add(assistant_msg)
    await db.commit()

    return ChatResponse(
        answer=result.answer,
        sources=result.sources,
        chunks_retrieved=result.chunks_retrieved,
    )


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ConversationResponse]:
    from sqlalchemy import select
    result = await db.execute(
        select(Conversation)
        .where(Conversation.owner_id == current_user.id)
        .order_by(Conversation.created_at.desc())
    )
    return list(result.scalars().all())