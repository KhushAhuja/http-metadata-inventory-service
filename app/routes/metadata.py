import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import HttpUrl

from app.models import MetadataRequest, MetadataRecord, AcceptedResponse
from app.services.metadata import fetch_and_store, get_stored_metadata

router = APIRouter()


def normalize_url(url: str) -> str:
    return str(HttpUrl(url))


@router.post("/metadata", response_model=MetadataRecord, status_code=201)
async def create_metadata(request: MetadataRequest):
    url = str(request.url)
    try:
        record = await fetch_and_store(url)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request to target URL timed out.")
    except httpx.RequestError as e:
        raise HTTPException(status_code=400, detail=f"Could not reach URL: {e}")
    return record


@router.get("/metadata", status_code=200)
async def get_metadata(url: str, background_tasks: BackgroundTasks):
    url = normalize_url(url)
    existing = await get_stored_metadata(url)

    if existing:
        return existing

    background_tasks.add_task(fetch_and_store, url)
    return JSONResponse(
        status_code=202,
        content=AcceptedResponse(
            message="Metadata not found. Collection has been scheduled.",
            url=url,
        ).model_dump(),
    )
