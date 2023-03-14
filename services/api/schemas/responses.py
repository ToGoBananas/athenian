from pydantic import BaseModel


class Message(BaseModel):
    message: str


class ForbiddenMessage(BaseModel):
    detail: str = "Not authenticated"


class BadRequestMessage(BaseModel):
    detail: str = "Bad request"


class NotFoundMessage(BaseModel):
    detail: str
