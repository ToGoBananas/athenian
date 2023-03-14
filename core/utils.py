import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal

import orjson
from pydantic import BaseModel


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ImmutableModel(BaseModel):
    class Config:
        frozen = True


def default_json(obj):
    if isinstance(obj, Decimal):
        if len(str(obj)) > 10:
            return str(obj)
        else:
            return float(obj)

    if isinstance(obj, set):
        return tuple(obj)

    if isinstance(obj, datetime):
        return obj.isoformat()

    raise TypeError


def orjson_dumps(v, *, option=orjson.OPT_NON_STR_KEYS) -> bytes:
    try:
        return orjson.dumps(v, option=option, default=default_json)
    except TypeError:  # fallback for big int
        return json.dumps(v, default=default_json).encode("utf-8")


def set_max_workers_for_loop(loop, max_workers=6):
    loop.set_default_executor(ThreadPoolExecutor(max_workers=max_workers))


def get_event_loop_policy():
    try:
        import uvloop
    except ImportError:
        return None

    return uvloop.EventLoopPolicy()
