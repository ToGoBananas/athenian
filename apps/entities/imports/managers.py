from fastapi import UploadFile

from apps.entities.base import BaseManager
from apps.entities.imports.validator import ImportValidator
from apps.entities.teams.managers import TeamDataManager
from apps.entities.teams.managers import TeamManager
from apps.entities.teams.schemas import TeamMetricCreate
from core.contexts import PROJECT_ID
from core.redis import RedisLockClient
from db import get_database
from db.models import imports


class ImportManager(BaseManager):
    validator: ImportValidator = ImportValidator
    table_model = imports

    @staticmethod
    def _get_lock():
        return RedisLockClient.get(f"import:{PROJECT_ID.get()}")

    async def create(self, file: UploadFile):
        async with self._get_lock():
            metrics, teams = await self.validator.validate_create(file)
            async with get_database().transaction():
                teams_db = await self._create_missing_teams(teams)
                await self.queries.create(filename=file.filename)
                await TeamDataManager().create(
                    [TeamMetricCreate(**metric.dict(), team_id=teams_db[metric.team]) for metric in metrics]
                )

    @classmethod
    async def _create_missing_teams(cls, teams: set[str]):
        teams_db = await TeamManager().queries.get_entities(
            filters={"name__in": teams, "project_id": PROJECT_ID.get()}, return_fields={"name"}
        )
        team_names_db = [team["name"] for team in teams_db]
        missing_teams = [team for team in teams if team not in team_names_db]
        await TeamManager().create(missing_teams)
        teams_db = await TeamManager().queries.get_entities(
            filters={"name__in": teams, "project_id": PROJECT_ID.get()}, return_fields={"name", "id"}
        )
        return {team["name"]: team["id"] for team in teams_db}
