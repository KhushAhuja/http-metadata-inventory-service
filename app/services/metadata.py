from datetime import datetime, timezone

import httpx

from app.config import settings
from app.database import get_database
from app.models import MetadataRecord


async def fetch_and_store(url: str) -> dict:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url, timeout=settings.request_timeout)

    record = MetadataRecord(
        url=url,
        status_code=response.status_code,
        headers=dict(response.headers),
        cookies=dict(response.cookies),
        page_source=response.text,
        fetched_at=datetime.now(timezone.utc),
    )

    db = get_database()
    await db["metadata"].find_one_and_replace(
        {"url": url},
        record.model_dump(),
        upsert=True,
    )

    return record.model_dump()


async def get_stored_metadata(url: str) -> dict | None:
    db = get_database()
    return await db["metadata"].find_one({"url": url}, {"_id": 0})
