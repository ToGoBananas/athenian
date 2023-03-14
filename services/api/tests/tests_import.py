from pathlib import Path

from starlette import status

from apps.entities.teams.managers import TeamDataManager
from apps.entities.teams.managers import TeamManager
from services.api.main import app


async def test_import_from_file_provided(client):
    files = {"file": open(Path(__file__).resolve().parent.joinpath("data.csv"), "rb")}
    response = await client.post(app.url_path_for("import_create"), files=files)
    assert response.status_code == status.HTTP_201_CREATED
    assert await TeamManager().queries.is_exists_entity()
    assert await TeamDataManager().queries.is_exists_entity()
