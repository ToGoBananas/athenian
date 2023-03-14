from pathlib import Path

import pytest
from starlette import status

from apps.entities.teams.managers import TeamDataManager
from apps.entities.teams.managers import TeamManager
from services.api.main import app


FILES_DIR = Path(__file__).resolve().parent.joinpath("test_files")


async def test_import_from_file_provided(client):
    files = {"file": open(FILES_DIR.joinpath("data.csv"), "rb")}
    response = await client.post(app.url_path_for("import_create"), files=files)
    assert response.status_code == status.HTTP_201_CREATED
    assert await TeamManager().queries.is_exists_entity()
    assert await TeamDataManager().queries.is_exists_entity()


@pytest.mark.parametrize("filename", [f"invalid_file_{i}.csv" for i in range(1, 6)])
async def test_invalid_import(client, filename: str):
    files = {"file": open(FILES_DIR.joinpath(filename), "rb")}
    response = await client.post(app.url_path_for("import_create"), files=files)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
