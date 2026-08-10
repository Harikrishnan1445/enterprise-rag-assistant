from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import *
from app.core.config import settings
from app.db.session import get_db
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.documents import router as documents_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(documents_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@app.get("/health/db")
async def health_check_db(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}