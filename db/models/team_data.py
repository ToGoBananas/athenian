from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import Identity
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import UniqueConstraint

from db import metadata
from db.utils import project_id_column
from db.utils import TimeStampedFields

__all__ = ["team", "team_stats", "team_data"]

team = Table(
    "team",
    metadata,
    Column("id", Integer, Identity(always=True), primary_key=True),
    project_id_column(),
    Column("name", String(length=255), nullable=False),
    *TimeStampedFields().all,
    UniqueConstraint("project_id", "name", name="team_unique"),
)


team_stats = Table(
    "team_stats",
    metadata,
    Column("id", Integer, Identity(always=True), primary_key=True),
    Column("team_id", Integer, ForeignKey("team.id", name="team_id_fk", ondelete="RESTRICT"), unique=True),
    project_id_column(),
    *TimeStampedFields().all,
)


team_data = Table(
    "team_data",
    metadata,
    Column("id", Integer, Identity(always=True), primary_key=True),
    Column("team_id", Integer, ForeignKey("team.id", name="team_id_fk", ondelete="RESTRICT"), nullable=False),
    Column("date", Date(), nullable=False),
    Column("review_time", Integer(), nullable=False),
    Column("merge_time", Integer(), nullable=False),
    project_id_column(),
    *TimeStampedFields().all,
    UniqueConstraint("team_id", "date", name="team_data_unique"),
)
