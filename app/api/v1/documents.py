import uuid

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    service = DocumentService(db)
    return await service.upload(current_user.id, file)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[DocumentResponse]:
    service = DocumentService(db)
    return await service.list_owned(current_user.id)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    service = DocumentService(db)
    return await service.get_owned(document_id, current_user.id)


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> None:
    service = DocumentService(db)
    await service.delete_owned(document_id, current_user.id)