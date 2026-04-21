from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import connect_db, close_db
from app.routes.metadata import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="HTTP Metadata Inventory Service",
    description="Collects and stores HTTP headers, cookies, and page source for any given URL.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
