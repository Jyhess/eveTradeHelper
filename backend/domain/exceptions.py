"""
Custom exceptions for EVE API client
"""


class EveAPIError(Exception):
    """Base exception for EVE API errors"""

    def __init__(self, message: str, status_code: int | None = None, url: str | None = None):
        """
        Initialize the exception

        Args:
            message: Error message
            status_code: HTTP status code (if applicable)
            url: URL that caused the error (if applicable)
        """
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class BadRequestError(EveAPIError):
    """Exception for 400 Bad Request errors"""

    def __init__(self, message: str, url: str | None = None):
        super().__init__(message, status_code=400, url=url)


class NotFoundError(EveAPIError):
    """Exception for 404 Not Found errors"""

    def __init__(self, message: str, url: str | None = None):
        super().__init__(message, status_code=404, url=url)


class ClientError(EveAPIError):
    """Exception for other 4xx client errors"""

    def __init__(self, message: str, status_code: int, url: str | None = None):
        super().__init__(message, status_code=status_code, url=url)


class ServerError(EveAPIError):
    """Exception for 5xx server errors"""

    def __init__(self, message: str, status_code: int, url: str | None = None):
        super().__init__(message, status_code=status_code, url=url)
