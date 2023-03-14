from apps.entities.base import BaseManager
from apps.entities.teams.schemas import TeamMetricCreate
from db.models import team
from db.models import team_data


class TeamManager(BaseManager):
    table_model = team

    async def create(self, names: list[str]):
        return await self.queries.bulk_create([{"name": name} for name in names])


class TeamDataManager(BaseManager):
    table_model = team_data

    async def create(self, entities: list[TeamMetricCreate]):
        return await self.queries.bulk_create([entity.dict() for entity in entities])
