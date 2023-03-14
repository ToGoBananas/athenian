import datetime

from pydantic import conint

from core.types import EntityId
from core.utils import ImmutableModel


class TeamMetricCreate(ImmutableModel):
    review_time: conint(ge=0)
    team_id: EntityId
    date: datetime.date
    merge_time: conint(ge=0)
