"""
Utility functions for the WhisperTrace API.
"""

from logging import Logger


def handle_exception_impl(
    exception: Exception,
    logger: Logger,
) -> tuple[dict, int]:
    """
    Handle exceptions thrown during execution.

    Args:
        exception (Exception): The exception that was thrown.
        logger (Logger): The logger to log the error message.

    Returns:
        tuple[dict, int]: The error response and the HTTP status code.
    """
    error_description = exception.args[0] if exception.args else "Internal server error"
    error_code = exception.error_code if hasattr(exception, "error_code") else 500
    error_detail = exception.detail if hasattr(exception, "detail") else None

    exception_to_return = {
        "code": error_code,
        "description": error_description,
    }

    if error_detail:
        exception_to_return["detail"] = error_detail

    logger.error("An error occurred: %s", error_description)

    return exception_to_return, error_code