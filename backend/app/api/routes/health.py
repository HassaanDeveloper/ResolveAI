from fastapi import APIRouter, Request
from app.core.config import settings


router = APIRouter()


@router.get("/")
async def health_check(request: Request):
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }