import asyncio

from brotli_asgi import BrotliMiddleware
from fastapi import FastAPI
from fastapi import HTTPException

from core.utils import set_max_workers_for_loop
from db import get_database
from services.api.utils import ORJSONResponse
from services.api.v1.team_data.endpoints import router


app = FastAPI(
    default_response_class=ORJSONResponse,
    docs_url="/core/public/v1/docs",
    openapi_url="/core/public/v1/openapi.json",
)
app.add_middleware(BrotliMiddleware)

app.include_router(router, prefix="/import", tags=["import"])


@app.exception_handler(HTTPException)
async def validation_exception_handler(request, exc):
    headers = getattr(exc, "headers", None)

    return ORJSONResponse(
        content={"detail": exc.detail},
        status_code=exc.status_code,
        headers=headers or None,
    )


@app.on_event("startup")
async def startup():
    set_max_workers_for_loop(asyncio.get_running_loop())
    await get_database().connect()
