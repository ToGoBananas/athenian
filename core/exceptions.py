from typing import Any

from fastapi import HTTPException
from starlette import status


class HttpBaseException(HTTPException):
    message = None

    def __init__(self, detail: Any = None, headers: dict[str, Any] | None = None):
        super().__init__(status_code=self.status_code, detail=detail or self.message, headers=headers)


class BadRequestException(HttpBaseException):
    status_code = status.HTTP_400_BAD_REQUEST


class NotFoundException(HttpBaseException):
    status_code = status.HTTP_404_NOT_FOUND


class ConflictException(HttpBaseException):
    status_code = status.HTTP_409_CONFLICT
