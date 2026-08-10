import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository

ALLOWED_TYPES = set(settings.allowed_file_types.split(","))


class DocumentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = DocumentRepository(db)

    async def upload(self, owner_id: uuid.UUID, file: UploadFile) -> Document:
        ext = (file.filename or "").split(".")[-1].lower()
        if ext not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '.{ext}' not allowed. Allowed: {', '.join(ALLOWED_TYPES)}",
            )

        content = await file.read()
        size_bytes = len(content)
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if size_bytes == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if size_bytes > max_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File exceeds max size of {settings.max_upload_size_mb}MB.",
            )

        storage_dir = Path(settings.storage_path)
        storage_dir.mkdir(parents=True, exist_ok=True)
        unique_name = f"{uuid.uuid4()}.{ext}"
        file_path = storage_dir / unique_name

        with open(file_path, "wb") as f:
            f.write(content)

        return await self.repo.create(
            owner_id=owner_id,
            filename=file.filename or unique_name,
            file_type=ext,
            file_size_bytes=size_bytes,
            storage_path=str(file_path),
        )

    async def get_owned(self, document_id: uuid.UUID, owner_id: uuid.UUID) -> Document:
        doc = await self.repo.get_by_id(document_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Document not found.")
        if str(doc.owner_id) != str(owner_id):
            raise HTTPException(status_code=403, detail="You do not own this document.")
        return doc

    async def list_owned(self, owner_id: uuid.UUID) -> list[Document]:
        return await self.repo.list_by_owner(owner_id)

    async def delete_owned(self, document_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        doc = await self.get_owned(document_id, owner_id)
        Path(doc.storage_path).unlink(missing_ok=True)
        await self.repo.delete(doc)