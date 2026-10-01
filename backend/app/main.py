from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import (
    ResolveAIException,
    resolveai_exception_handler,
    generic_exception_handler,
)
from app.core.middleware import RequestIDMiddleware
from app.api.router import api_router


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ResolveAI backend is starting")
    yield
    logger.info("ResolveAI backend is shutting down")


def create_app() -> FastAPI:
    setup_logging("DEBUG" if settings.DEBUG else "INFO")

    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        lifespan=lifespan,
        docs_url=f"{settings.API_PREFIX}/docs",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
    )

    app.add_middleware(RequestIDMiddleware)

    app.add_exception_handler(ResolveAIException, resolveai_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


app = create_app()