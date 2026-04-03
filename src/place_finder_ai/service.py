from __future__ import annotations

from place_finder_ai.models import FindPlaceRequest, FindPlaceResponse, LocationHint
from place_finder_ai.providers import GeoProvider, VisionProvider


class PlaceFinderService:
    def __init__(self, vision: VisionProvider, geo: GeoProvider):
        self.vision = vision
        self.geo = geo

    async def find_places(self, request: FindPlaceRequest) -> FindPlaceResponse:
        vision_results = await self.vision.describe_image(request.image_url, request.openai_prompt)

        # Basic heuristic extraction from request context + detected text.
        combined_text = " ".join([r.text for r in vision_results] + [request.user_context or ""])
        seed_queries = self._build_seed_queries(combined_text)

        hints: list[LocationHint] = []
        for seed in seed_queries:
            for candidate in await self.geo.geocode(seed):
                hints.append(
                    LocationHint(
                        source=candidate["source"],
                        label=candidate["label"],
                        latitude=candidate.get("latitude"),
                        longitude=candidate.get("longitude"),
                        confidence=0.45,
                        reasoning=f"Matched seed query '{seed}' from visual/context clues.",
                    )
                )

        if not hints:
            hints.append(
                LocationHint(
                    source="heuristic",
                    label="Unknown park with trees and bench",
                    confidence=0.1,
                    reasoning="No API candidates found. Add richer context and keys.",
                )
            )

        return FindPlaceResponse(
            query_summary="Ran vision + geocoding across multiple APIs.",
            hints=hints[:10],
            next_steps=[
                "Add memory clues (city, season, language on signs).",
                "Upload 3-5 photos from the same day for better triangulation.",
                "Enable additional providers in .env (Mapbox, SerpAPI, OpenAI Vision).",
            ],
        )

    def _build_seed_queries(self, text: str) -> list[str]:
        # Keep this conservative to avoid geocoding random tokens.
        lower = text.lower()
        seeds = []
        if "park" in lower or "bench" in lower:
            seeds.append("public park")
        if "eucalyptus" in lower:
            seeds.append("eucalyptus park")
        if "lake" in lower:
            seeds.append("lake park")
        if not seeds:
            seeds.append("family park")
        return seeds
