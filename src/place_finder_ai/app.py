from __future__ import annotations

import httpx
from fastapi import FastAPI

from place_finder_ai.models import FindPlaceRequest, FindPlaceResponse
from place_finder_ai.providers import GeoProvider, VisionProvider
from place_finder_ai.service import PlaceFinderService

app = FastAPI(title="Place Finder AI", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/find-place", response_model=FindPlaceResponse)
async def find_place(payload: FindPlaceRequest) -> FindPlaceResponse:
    async with httpx.AsyncClient() as client:
        service = PlaceFinderService(VisionProvider(client), GeoProvider(client))
        return await service.find_places(payload)
