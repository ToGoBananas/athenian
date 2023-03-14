import os

from core.utils import ImmutableModel


class DBConfig(ImmutableModel):
    host: str = os.getenv("DB_HOST", "localhost")
    password: str = os.getenv("DB_PASSWORD", "password")
    user: str = os.getenv("DB_USER", "user")
    database: str | None = os.getenv("DB_NAME", "database")
    port: int = os.getenv("DB_PORT", 5434)
    pool_size: int = 20

    @classmethod
    def get_default(cls):
        return DBConfig()

    @property
    def url(self):
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode=disable"
