"""Centralized exception -> HTTP response mapping.

One place decides the wire format for errors, so every route returns a
consistent `{"error": {"code": ..., "message": ...}}` shape instead of
each handler improvising its own.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

# Use the literal code rather than starlette.status's constant: the constant
# name itself has churned across Starlette versions (HTTP_422_UNPROCESSABLE_ENTITY
# vs HTTP_422_UNPROCESSABLE_CONTENT), and 422 is an unambiguous, stable HTTP code.
HTTP_422_VALIDATION_ERROR = 422
HTTP_500_INTERNAL_ERROR = 500


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "app_error",
            extra={"error_code": exc.code, "path": request.url.path},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.info("validation_error", extra={"path": request.url.path})
        return JSONResponse(
            status_code=HTTP_422_VALIDATION_ERROR,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request failed validation.",
                    "details": jsonable_encoder(exc.errors()),
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Never leak internals (stack traces, exception text) to the client;
        # full detail goes to logs only, keyed by the request path/time.
        logger.exception("unhandled_exception", extra={"path": request.url.path})
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_ERROR,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred.",
                }
            },
        )
