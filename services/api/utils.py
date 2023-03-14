import typing
from typing import Any

import orjson
from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import ORJSONResponse as ORJSONResp
from starlette import status
from starlette.background import BackgroundTask

from core.utils import orjson_dumps
from services.api import deps
from services.api.schemas.responses import BadRequestMessage
from services.api.schemas.responses import ForbiddenMessage
from services.api.schemas.responses import NotFoundMessage


class ORJSONResponse(ORJSONResp):
    def __init__(
        self,
        content: typing.Any = None,
        status_code: int = 200,
        headers: typing.Optional[dict] = None,
        media_type: typing.Optional[str] = None,
        background: typing.Optional[BackgroundTask] = None,
    ) -> None:
        super().__init__(content, status_code, headers, media_type, background)

    def render(self, content: Any) -> bytes:
        return orjson_dumps(content, option=orjson.OPT_NON_STR_KEYS | orjson.OPT_UTC_Z | orjson.OPT_NAIVE_UTC)


def get_router():
    return APIRouter(
        responses={
            status.HTTP_400_BAD_REQUEST: {"model": BadRequestMessage},
            status.HTTP_401_UNAUTHORIZED: {"model": ForbiddenMessage},
            status.HTTP_403_FORBIDDEN: {"model": ForbiddenMessage},
            status.HTTP_404_NOT_FOUND: {"model": NotFoundMessage},
        },
        dependencies=[Depends(deps.project_id_for_rest)],
    )
