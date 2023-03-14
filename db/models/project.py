from sqlalchemy import Column
from sqlalchemy import SMALLINT
from sqlalchemy import String
from sqlalchemy import Table

from db import metadata
from db.utils import TimeStampedFields

__all__ = [
    "project",
]

project = Table(
    "project",
    metadata,
    Column("id", SMALLINT, primary_key=True),
    Column("name", String(length=25), unique=True),
    *TimeStampedFields().all,
)
