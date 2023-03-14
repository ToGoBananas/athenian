from db import get_database
from db.queries.base import BaseQuery


class BaseValidator:
    def __init__(self, queries: BaseQuery):
        self.queries = queries


class BaseManager:
    db_client = get_database()
    queries: BaseQuery = BaseQuery
    validator = BaseValidator
    table_model = None

    def __init__(self):
        self.queries = self.queries(conn=self.db_client, table_model=self.table_model)
        self.validator = self.validator(self.queries)
