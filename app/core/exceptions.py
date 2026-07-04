"""Domain-level exceptions.

Services and repositories raise these instead of framework-specific
errors, keeping business logic decoupled from FastAPI. The API layer maps
each one to an HTTP response in a single centralized exception handler
(see app.api.error_handlers).
"""


class AppError(Exception):
    """Base class for expected, actionable errors with a fixed HTTP mapping."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class BatchNotFoundError(AppError):
    status_code = 404
    code = "batch_not_found"


class BatchTooLargeError(AppError):
    status_code = 422
    code = "batch_too_large"
