from functools import partial

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import func


class TimeStampedFields:
    _created = partial(Column, "created", DateTime(timezone=False), server_default=func.now())
    _modified = partial(Column, "modified", DateTime(timezone=False), onupdate=func.now())

    @property
    def created(self):
        return self._created()

    @property
    def modified(self):
        return self._modified()

    @property
    def all(self):
        return self.created, self.modified


def project_id_column():
    return Column("project_id", ForeignKey("project.id", ondelete="CASCADE", name="project_id_fk"), nullable=False)
