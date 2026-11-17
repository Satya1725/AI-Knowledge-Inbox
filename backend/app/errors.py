"""Application errors.

Every error we raise on purpose is an AppError. The handler in main.py turns
it into a JSON response: {"error": {"code": ..., "message": ...}}.
"""


class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class FetchError(AppError):
    """The URL could not be downloaded or had no usable content."""

    status_code = 422
    code = "fetch_failed"


class EmptyContentError(AppError):
    status_code = 422
    code = "empty_content"


class ProviderNotConfiguredError(AppError):
    status_code = 503
    code = "provider_not_configured"


class AIProviderError(AppError):
    """The upstream LLM / embedding API failed."""

    status_code = 502
    code = "ai_provider_error"
