from __future__ import annotations

from pydantic import BaseModel, Field


class LocationHint(BaseModel):
    source: str
    label: str
    latitude: float | None = None
    longitude: float | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class FindPlaceRequest(BaseModel):
    image_url: str
    user_context: str | None = None
    openai_prompt: str = (
        "Describe clues about where this photo might have been taken. "
        "Include visible features (trees, bench, surfaces, urban/rural indicators)."
    )


class FindPlaceResponse(BaseModel):
    query_summary: str
    hints: list[LocationHint]
    next_steps: list[str]
