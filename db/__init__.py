import asyncio
import enum
import typing
from contextlib import contextmanager
from contextlib import nullcontext
from contextvars import ContextVar

import databases
import sqlalchemy
from databases import Database
from sqlalchemy import create_engine

from core import settings
from core.settings import DBConfig

config = DBConfig().get_default()
engine = create_engine(config.url)


metadata = sqlalchemy.MetaData()


class DatabaseTypeEnum(enum.Enum):
    DEFAULT = "default"
    NO_ROLLBACK = "no_rollback"  # hacks for websocket tests


class _DbRouter:
    current: DatabaseTypeEnum = DatabaseTypeEnum.DEFAULT
    prev: DatabaseTypeEnum = None
    cache = {}

    @contextmanager
    def switch(self, t: DatabaseTypeEnum):
        if self.prev is not None:
            raise Exception("database already switched")

        self.current, prev = t, self.current
        try:
            yield
        finally:
            self.current, prev = prev, None

    def get(self):
        db = self.cache.get(self.current)
        if not db:
            db = self._new_database(force_rollback=settings.TESTING and self.current != DatabaseTypeEnum.NO_ROLLBACK)
            self.cache[self.current] = db
        return db

    def _new_database(self, disable_jit=True, force_rollback=False):
        server_settings = {}

        if disable_jit:
            server_settings["jit"] = "off"

        return Database(
            config.url,
            min_size=5,
            max_size=config.pool_size,
            force_rollback=force_rollback,
            server_settings=server_settings,
        )


_db_router = _DbRouter()
del _DbRouter

switch_database = _db_router.switch
get_database = _db_router.get
