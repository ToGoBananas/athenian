from fastapi import Header

from core.contexts import PROJECT_ID
from core.exceptions import BadRequestException
from core.settings.projects import PROJECTS
from core.types import EntityId


async def project_id_for_rest(project_id: EntityId = Header()):
    if project_id not in PROJECTS:  # let's imagine that we cached projects from the database to this variable
        raise BadRequestException(detail="Invalid project_id")
    PROJECT_ID.set(project_id)
    return project_id
