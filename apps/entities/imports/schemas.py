import datetime

from pydantic import conint
from pydantic import constr

from core.utils import ImmutableModel


class TeamMetricCSV(ImmutableModel):
    review_time: conint(ge=0)
    team: constr(min_length=1, max_length=255)
    date: datetime.date
    merge_time: conint(ge=0)
