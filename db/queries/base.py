import asyncio
import enum
import itertools
from datetime import timedelta
from functools import wraps
from typing import Any

from asyncpg.exceptions import UniqueViolationError
from databases.interfaces import Record
from pydantic import NonNegativeInt
from sqlalchemy import all_
from sqlalchemy import any_
from sqlalchemy import asc
from sqlalchemy import Column
from sqlalchemy import desc
from sqlalchemy import exists
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy import select
from sqlalchemy import Table
from sqlalchemy import UniqueConstraint
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.expression import bindparam
from sqlalchemy.sql.expression import delete
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.functions import Function

from core.contexts import PROJECT_ID
from core.exceptions import ConflictException
from core.types import NonEmptyStr
from db import Database


class BaseQuery:
    index_keys: set[str] | None = None
    main_foreign_key: Column | None = None

    # https://github.com/MagicStack/asyncpg/blob/9825bbb61140e60489b8d5649a288d1f67c0ef9f/asyncpg/protocol/prepared_stmt.pyx#L125
    PSQL_QUERY_ALLOWED_MAX_ARGS = 32767

    FN: str = "__fn"
    ORDER_BY: str = "-"
    ORDER_BY_LABEL = "__label"

    @staticmethod
    def date__with_offset(column, offset):
        return func.date(column + timedelta(minutes=offset))

    @staticmethod
    def __overlap(column, value):
        try:
            return column.overlap(value)
        except AttributeError:  # FIXME: failed test_admin_markets_settings_create_call_200 test
            return text(f"{column} && array[{value}]")

    _select_conditions = {
        "__contains__in": lambda column, value: column.like(any_([contains(x) for x in value])),
        "__icontains__in": lambda column, value: column.ilike(any_([contains(x) for x in value])),
        "__icontains__not_in": lambda column, value: ~column.ilike(all_([contains(x) for x in value])),
        "__coalesce__icontains_in_pair": lambda columns, value: func.coalesce(columns[0], columns[1]).ilike(
            any_([contains(x) for x in value])
        ),
        "__icontains__in_pair": lambda columns, value: columns[0].ilike(any_([contains(x) for x in value]))
        | columns[1].ilike(any_([contains(x) for x in value])),
        "__contains": lambda column, value: column.like(contains(value)),
        "__icontains": lambda column, value: column.ilike(contains(value)),
        "__ilike": lambda column, value: column.ilike(value),
        "__coalesce__in__in_pair": lambda columns, value: func.coalesce(columns[0], columns[1]).in_(value),
        "__in": lambda column, value: column.in_(value),
        "__in_if_exists": lambda column, value: column.in_(value) | column.is_(None),
        "__in_subquery": lambda column, value: column.in_(value),  # same that "__in" but for internal use # TODO delete
        "__not_in": lambda column, value: ~column.in_(value),
        "__not_in_subquery": lambda column, value: ~column.in_(
            value
        ),  # same that "__not_in" but for internal use # TODO delete
        "__in_pair": lambda columns, value: columns[0].in_(value) | columns[1].in_(value),
        "__date__lt_if_exists": lambda column, value: column.is_(None) | (func.date(column) < value),
        "__date__gt_if_exists": lambda column, value: column.is_(None) | (func.date(column) > value),
        "__date__lt": lambda column, value: func.date(column) < value,
        "__date__gt": lambda column, value: func.date(column) > value,
        "__date__lte": lambda column, value: func.date(column) <= value,
        "__date__gte": lambda column, value: func.date(column) >= value,
        "__date": lambda column, value: func.date(column) == value,
        "__date__with_offset__lte": lambda column, value: BaseQuery.date__with_offset(column, value[0]) <= value[1],
        "__date__with_offset__lt": lambda column, value: BaseQuery.date__with_offset(column, value[0]) < value[1],
        "__date__with_offset__gte": lambda column, value: BaseQuery.date__with_offset(column, value[0]) >= value[1],
        "__date__with_offset__gt": lambda column, value: BaseQuery.date__with_offset(column, value[0]) > value[1],
        "__date__with_offset": lambda column, value: BaseQuery.date__with_offset(column, value[0])
        == value[1],  # value like: (-60, date)
        "__gt": lambda column, value: column > value,
        "__lt": lambda column, value: column < value,
        "__gte": lambda column, value: column >= value,
        "__lte": lambda column, value: column <= value,
        "__has_any_keys": lambda column, value: text(f"{column} ?| array[{enum_to_array(value)}]"),
        "__isnull": lambda column, value: column.is_(None) if value else column.isnot(None),
        "__jsonb_isnull": lambda column, value: column == "null" if value else column != "null",
        "__overlap": __overlap,
        "__include_all_if_exists": lambda column, value: column.is_(None) | column.contains(value),
        "__include_all": lambda column, value: column.contains(value),
        "__include_any": lambda column, value: column.overlap(value),  # synonym of OVERLAP
        "__exclude_all": lambda column, value: column.is_(None) | ~column.contains(value),
        "__exclude_any": lambda column, value: column.is_(None) | ~column.overlap(value),
        "__coalesce__include_all_in_pair": lambda columns, value: func.coalesce(columns[0], columns[1]).contains(value),
        "__coalesce__include_any_in_pair": lambda columns, value: func.coalesce(columns[0], columns[1]).overlap(value),
        "__coalesce__exclude_all_in_pair": lambda columns, value: func.coalesce(columns[0], columns[1]).is_(None)
        | ~func.coalesce(columns[0], columns[1]).contains(value),
        "__coalesce__exclude_any_in_pair": lambda columns, value: func.coalesce(columns[0], columns[1]).is_(None)
        | ~func.coalesce(columns[0], columns[1]).overlap(value),
        "__include_all_in_pair": lambda columns, value: columns[0].contains(value) | columns[1].contains(value),
        "__include_any_in_pair": lambda columns, value: columns[0].overlap(value) | columns[1].overlap(value),
        "__exclude_all_in_pair": lambda columns, value: columns[0].is_(None)
        | ~columns[0].contains(value)
        | columns[1].is_(None)
        | ~columns[1].contains(value),
        "__exclude_any_in_pair": lambda columns, value: columns[0].is_(None)
        | ~columns[0].overlap(value)
        | columns[1].is_(None)
        | ~columns[1].overlap(value),
        "__date__gt_in_pair": lambda columns, values: (columns[0].isnot(None) & (func.date(columns[0]) > values[0]))
        | (columns[0].is_(None) & (func.date(columns[1]) >= values[1])),
        "__date__lt_in_pair": lambda columns, values: (columns[0].isnot(None) & (func.date(columns[0]) < values[0]))
        | (columns[0].is_(None) & (func.date(columns[1]) < values[1])),
        "*__or__*": lambda columns, value: or_(c == value for c in columns),
        "": lambda column, value: column == value,  # default
    }

    def __init__(self, *, conn: Database, table_model: Table) -> None:
        self.conn = conn

        self.table_model: Table = table_model

    def _get_index_keys(self) -> set:

        if self.index_keys:
            return self.index_keys

        if union_constraint := [i for i in self.table_model.constraints if isinstance(i, UniqueConstraint)]:
            return {column.name for column in union_constraint[0].columns}

        return {c.name for i in self.table_model.constraints if isinstance(i, PrimaryKeyConstraint) for c in i}

    def _set_project_id_to_kwargs(self, kwargs):
        if self.table_model.columns.get("project_id") is not None:
            if project_id := PROJECT_ID.get():
                kwargs.setdefault("project_id", project_id)

    def _get_columns(self, key_name: str) -> Any | list:
        columns = key_name.split("__or__")
        if len(columns) == 1:
            return self.table_model.columns.get(columns[0])
        elif all(col in self.table_model.columns for col in columns):
            return [self.table_model.columns[col] for col in columns]

    def filters(self, q, **kwargs) -> select:
        for key, value in (kwargs.get("filters") or {}).items():
            for suffix, condition in self._select_conditions.items():
                if column_name := get_column_name(key, suffix):
                    column = self._get_columns(column_name)
                    if column is not None:
                        q = q.where(condition(column, value))
                        break
        return q

    def filters_by_related_tables(self, q: select, filters: dict, tables_with_keys: dict[NonEmptyStr, Table]) -> select:

        for key, table_model in tables_with_keys.items():
            if _filters := {k.removeprefix(key): v for k, v in filters.items() if k.startswith(key)}:
                q = BaseQuery(table_model=table_model).filters(q=q, filters=_filters)

        return q

    def distinct(self, q, **kwargs) -> select:
        if kwargs.get("is_distinct"):
            q = q.distinct()
        return q

    def join_relations(self, q: select, **kwargs) -> select:
        key_fk = "_id_fk"

        for foreign_key in (fk for fk in self.table_model.foreign_keys if fk.name and fk.name.endswith(key_fk)):
            table_name = f"{foreign_key.name.removesuffix(key_fk)}__"

            if filters := {
                key.removeprefix(table_name): value
                for key, value in (kwargs.get("filters") or {}).items()
                if key.startswith(table_name)
            }:
                obj = BaseQuery(table_model=foreign_key.column.table)

                q = q.select_from(q.froms[0].join(obj.table_model))
                q = obj.filters(q=q, filters=filters)
                q = obj.join_relations(q=q, filters=filters)

        return q

    def order_by(self, q, **kwargs):
        for key in kwargs.get("order_by") or []:
            if key.startswith(self.ORDER_BY):
                k = key.removeprefix(self.ORDER_BY)
                if key.endswith(self.ORDER_BY_LABEL):
                    q = q.order_by(desc(k.removesuffix(self.ORDER_BY_LABEL)))
                else:
                    q = q.order_by(desc(self.table_model.columns[k]))
            else:
                if key.endswith(self.ORDER_BY_LABEL):
                    q = q.order_by(asc(key.removesuffix(self.ORDER_BY_LABEL)))
                else:
                    q = q.order_by(asc(self.table_model.columns[key.removeprefix(self.ORDER_BY)]))

        return q

    def create_jsonb_column(self, table: Table, columns: list[str]) -> Function:
        return func.json_build_object(text(",".join(f"'{column}', {table.columns[column]}" for column in columns)))

    def _select_query(self, **kwargs) -> select:

        return select(
            [
                self.table_model.columns[column]
                for column in kwargs.get("return_fields") or self.table_model.columns.keys()
            ]
        )

    def _values(self, q, **kwargs):
        values = {}

        for key, value in kwargs.get("values", {}).items():
            if col := get_column_name(key, self.FN):
                values[col] = value(self.table_model.columns[col])
            else:
                values[key] = value

        return q.values(**values)

    @staticmethod
    def convertor(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs) -> list[dict] | dict | None:
            response = await fn(*args, **kwargs)

            if isinstance(response, list):
                return [dict(db_entity) for db_entity in response]

            elif isinstance(response, Record):
                return dict(response)

        return wrapper

    async def get_entity(self, **kwargs) -> dict:
        q = self.prepare_query(**kwargs)

        return await self.get_entity_by_query(q=q)

    async def get_entities(self, limit: int = None, offset: int = None, **kwargs) -> list[dict]:
        q = self.prepare_query(**kwargs)

        return await self.get_entities_by_query(q=q, limit=limit, offset=offset)

    async def get_count(self, **kwargs) -> NonNegativeInt:
        q = select([self.table_model])
        q = self.filters(q=q, **kwargs)
        q = self.join_relations(q=q, **kwargs)

        return await self.conn.fetch_val(select([func.count()]).select_from(q.alias()))

    async def get_entities_ids(self, **kwargs) -> list[int]:
        q = select([func.array_agg(self.table_model.c.id)])
        q = self.filters(q=q, **kwargs)
        q = self.join_relations(q=q, **kwargs)

        return await self.conn.fetch_val(q) or []

    async def is_exists_entity(self, **kwargs) -> bool:
        q = select(self.table_model.primary_key.columns)
        q = self.filters(q=q, **kwargs)
        q = self.join_relations(q=q, **kwargs)

        return await self.conn.execute(select([exists(q)]))

    async def delete(self, filters: dict, return_id=True) -> int:
        q = delete(self.table_model)
        q = self.filters(q=q, filters=filters)
        if return_id:
            q = q.returning(self.table_model.c.id)
        return await self.conn.fetch_val(q)

    @convertor
    async def bulk_create(self, values: list[dict], is_returning=True) -> list[dict] | None:
        if self.table_model.columns.get("project_id") is not None:
            if project_id := PROJECT_ID.get():
                for x in values:
                    x.setdefault("project_id", project_id)

        if self.PSQL_QUERY_ALLOWED_MAX_ARGS > len(values) * len(values[0]):

            q = insert(self.table_model).values(values)

            try:
                return await (
                    self.conn.fetch_all(q.returning(self.table_model)) if is_returning else self.conn.execute(q)
                )
            except UniqueViolationError as e:
                raise ConflictException(e.detail)

        queries_in_batch = int(self.PSQL_QUERY_ALLOWED_MAX_ARGS / len(values[0]))
        tasks = []

        for args in (values[x : x + queries_in_batch] for x in range(0, len(values), queries_in_batch)):
            q = insert(self.table_model).values(args)
            if is_returning:
                q = self.conn.fetch_all(q.returning(self.table_model))
            else:
                q = self.conn.execute(q)
            tasks.append(q)

        try:
            db_queries = await asyncio.gather(*tasks)
        except UniqueViolationError as e:
            raise ConflictException(e.detail)

        if is_returning:
            return list(itertools.chain(*db_queries))

    async def bulk_update(self, values: list[dict]) -> None:
        if self.table_model.columns.get("project_id") is not None:
            if PROJECT_ID.get():
                for val in values:
                    val.pop("project_id", None)
        q = (
            update(self.table_model)
            .where(self.table_model.c.id == bindparam("id"))
            .values(**{key: bindparam(key) for key in values[0].keys() if key not in ("id", "project_id")})
        )

        await self.conn.execute_many(str(q), values)

    async def update(self, is_returning=True, **kwargs) -> dict | None:
        q = update(self.table_model)
        q = self.filters(q=q, **kwargs)
        q = self._values(q=q, **kwargs)
        if is_returning:
            return await self.get_entity_by_query(q.returning(self.table_model))
        return await self.conn.execute(q)

    async def update_entities_by_query(self, q: update):
        return await self.conn.fetch_all(q)

    async def create(self, is_returning: bool = True, **kwargs) -> dict | None:
        self._set_project_id_to_kwargs(kwargs)
        q = insert(self.table_model).values(**kwargs)

        try:
            if is_returning:
                return await self.get_entity_by_query(q.returning(self.table_model))

            await self.conn.execute(q)

        except UniqueViolationError as e:
            raise ConflictException(e.detail)

    async def upsert(self, on_conflict="update", **kwargs) -> dict:
        if "modified" in self.table_model.columns:
            kwargs.update({"modified": func.now()})
        self._set_project_id_to_kwargs(kwargs)

        index_keys = self._get_index_keys()

        statement = insert(self.table_model).values(**kwargs)

        if on_conflict == "update":
            set_clause = {key: getattr(statement.excluded, key) for key in kwargs.keys() if key not in index_keys}
            return await self.get_entity_by_query(
                statement.returning(self.table_model).on_conflict_do_update(index_elements=index_keys, set_=set_clause)
            )
        return await self.get_entity_by_query(statement.returning(self.table_model).on_conflict_do_nothing())

    @convertor
    async def get_entity_by_query(self, q: select) -> dict:
        return await self.conn.fetch_one(q)

    async def get_value_by_query(self, q: select) -> Any:
        return await self.conn.fetch_val(q)

    @convertor
    async def get_entities_by_query(self, q: select, limit: int = None, offset: int = None) -> list[dict]:
        return await self.conn.fetch_all(q.limit(limit=limit).offset(offset=offset))

    async def get_count_by_query(self, q: select) -> int:
        return await self.conn.fetch_val(select([func.count()]).select_from(q.alias(name="count_subquery")))

    async def is_exists_entity_by_query(self, q: exists) -> bool:
        return await self.conn.execute(select([q]))

    async def get_entities_with_count(self, q: select, limit: int, offset: int) -> (list, int):
        return await asyncio.gather(
            self.get_entities_by_query(q=q, limit=limit, offset=offset),
            self.get_count_by_query(q=q),
        )

    async def get_value(self, column: str, **kwargs) -> Any:
        q = select(self.table_model.columns[column])

        q = self.filters(q=q, **kwargs)
        q = self.join_relations(q=q, **kwargs)
        q = self.order_by(q=q, **kwargs)
        return await self.get_value_by_query(q)

    async def upsert_on_conflict_do_nothing(self, **kwargs) -> int:
        self._set_project_id_to_kwargs(kwargs)
        return await self.conn.execute(insert(self.table_model).values(**kwargs).on_conflict_do_nothing())

    async def get_max_priority(self, filters: dict) -> int:
        q = select(func.coalesce(func.max(self.table_model.c.priority), 0))

        q = self.filters(q=q, filters=filters)
        q = self.join_relations(q=q, filters=filters)

        return await self.get_value_by_query(q=q)

    def prepare_query(self, **kwargs) -> select:
        q = self._select_query(**kwargs)
        q = self.filters(q=q, **kwargs)
        q = self.join_relations(q=q, **kwargs)
        q = self.order_by(q=q, **kwargs)
        q = self.distinct(q=q, **kwargs)

        return q


def get_column_name(key, suffix) -> str:
    if key.endswith(suffix):
        return key.removesuffix(suffix)

    if suffix.startswith("*") and suffix.endswith("*") and suffix.removesuffix("*").removeprefix("*") in key:
        return key

    return ""


def contains(val: str):
    val = val.replace("\\", "\\\\")
    return f"%\\{val}%"


def enum_to_array(v: list[enum.Enum]) -> str:
    return ",".join(f"'{key.value}'" for key in v)
