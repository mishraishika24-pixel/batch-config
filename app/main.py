"""FastAPI application factory.

Kept intentionally thin: wiring only. Business logic lives in
``app.services``, data access in ``app.repositories``.
"""

import logging

from fastapi import FastAPI

from app.api.error_handlers import register_exception_handlers
from app.api.middleware import RequestLoggingMiddleware
from app.api.routes import batches, health
from app.core.config import get_settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title="Batch Processing Service",
        version="0.1.0",
        description="Submit batches of items for asynchronous processing.",
    )

    app.add_middleware(RequestLoggingMiddleware)

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(batches.router)

    logger.info("application_configured", extra={"app_env": settings.app_env})
    return app


app = create_app()
