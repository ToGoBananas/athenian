from fastapi import UploadFile
from starlette import status

from apps.entities.imports.managers import ImportManager
from services.api.utils import get_router

router = get_router()


@router.post(
    path="",
    operation_id="import_create",
    status_code=status.HTTP_201_CREATED,
)
async def import_create(
    file: UploadFile,
):
    return await ImportManager().create(file)
