from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)) -> UserResponse:
    return current_user


@router.get("", response_model=list[UserResponse])
async def list_all_users(
    admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
) -> list[UserResponse]:
    result = await db.execute(select(User))
    return list(result.scalars().all())