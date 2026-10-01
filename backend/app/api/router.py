from fastapi import APIRouter
from app.api.routes import health, resolutions, approvals, audit, dashboard, evaluation, knowledge


api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(resolutions.router, prefix="/resolutions", tags=["resolutions"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["evaluation"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])