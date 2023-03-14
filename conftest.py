import asyncio

import pytest
from httpx import AsyncClient

from db import DatabaseTypeEnum
from db import get_database
from db import switch_database
from services.api.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client(event_loop):
    """Test client for testing API."""
    http_client = AsyncClient(app=app, base_url="http://test", headers={"project-id": "1"})
    yield http_client
    await http_client.aclose()


@pytest.fixture(autouse=True)
async def db(event_loop):
    with switch_database(DatabaseTypeEnum.DEFAULT):
        async with get_database() as db:
            yield db
