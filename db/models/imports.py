from sqlalchemy import Column
from sqlalchemy import Identity
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table

from db import metadata
from db.utils import project_id_column
from db.utils import TimeStampedFields

__all__ = [
    "imports",
]

imports = Table(
    "imports",
    metadata,
    Column("id", Integer, Identity(always=True), primary_key=True),
    project_id_column(),
    Column("filename", String(length=255), nullable=False),
    TimeStampedFields().created,
)
