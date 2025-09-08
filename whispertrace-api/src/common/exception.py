"""
Custom exceptions for the application.
"""

class BaseWhisperTraceException(Exception):
    """
    Base exception for the project.
    """
    def __init__(
        self,
        message: str = "An error occurred.",
        error_code: int = 500,
        **detail_kwargs
    ):
        super().__init__(message)

        self.error_code = error_code

        if detail_kwargs and isinstance(detail_kwargs, dict):
            self.detail = detail_kwargs


class ClientException(BaseWhisperTraceException):
    """
    Exception class for when there is an error with the client.
    """

    def __init__(self, message: str = "Client error."):
        super().__init__(message, 400)


class ServerException(BaseWhisperTraceException):
    """
    Exception class for when there is an error with the server.
    """

    def __init__(self, message: str = "Server error."):
        super().__init__(message, 500)


class ObjectNotFoundException(BaseWhisperTraceException):
    """
    Exception raised when an object is not found.
    """

    def __init__(self, message: str = "Object not found."):
        super().__init__(message, 404)


class CorpusGenerationException(BaseWhisperTraceException):
    """
    Exception raised for errors in the corpus generation process.
    """

    def __init__(self, message: str = "Corpus generation error."):
        super().__init__(message, 500)


class WebScrapingException(BaseWhisperTraceException):
    """
    Exception raised for errors in web scraping.
    """

    def __init__(self, message: str = "Web scraping error."):
        super().__init__(message, 500)
