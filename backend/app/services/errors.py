from __future__ import annotations


class ServiceError(Exception):
    """An error whose message is safe to show to a visitor."""

    def __init__(self, code: str, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
