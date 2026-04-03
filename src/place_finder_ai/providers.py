from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass
class ProviderResult:
    source: str
    text: str


class VisionProvider:
    """Runs image understanding with whichever API keys are configured.

    Priority: OpenAI Vision -> Google Cloud Vision label detection.
    """

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def describe_image(self, image_url: str, prompt: str) -> list[ProviderResult]:
        results: list[ProviderResult] = []

        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            response = await self.client.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {openai_key}"},
                json={
                    "model": os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini"),
                    "input": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": prompt},
                                {
                                    "type": "input_image",
                                    "image_url": image_url,
                                },
                            ],
                        }
                    ],
                },
                timeout=45,
            )
            response.raise_for_status()
            body = response.json()
            text = body.get("output", [{}])
            flat = str(text)
            results.append(ProviderResult(source="openai_vision", text=flat))

        google_key = os.getenv("GOOGLE_VISION_API_KEY")
        if google_key:
            response = await self.client.post(
                f"https://vision.googleapis.com/v1/images:annotate?key={google_key}",
                json={
                    "requests": [
                        {
                            "image": {"source": {"imageUri": image_url}},
                            "features": [{"type": "LABEL_DETECTION", "maxResults": 20}],
                        }
                    ]
                },
                timeout=45,
            )
            response.raise_for_status()
            body = response.json()
            annotations = body.get("responses", [{}])[0].get("labelAnnotations", [])
            labels = [a.get("description", "") for a in annotations]
            results.append(
                ProviderResult(source="google_vision", text=", ".join(filter(None, labels)))
            )

        return results


class GeoProvider:
    """Geocodes candidate place names using several APIs when available."""

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def geocode(self, query: str) -> list[dict]:
        candidates: list[dict] = []

        mapbox_key = os.getenv("MAPBOX_TOKEN")
        if mapbox_key:
            response = await self.client.get(
                f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json",
                params={"access_token": mapbox_key, "limit": 3},
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            for item in data.get("features", []):
                candidates.append(
                    {
                        "source": "mapbox",
                        "label": item.get("place_name", query),
                        "latitude": item.get("center", [None, None])[1],
                        "longitude": item.get("center", [None, None])[0],
                    }
                )

        # Fallback: OpenStreetMap Nominatim (no key required)
        response = await self.client.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 3},
            headers={"User-Agent": "place-finder-ai/0.1"},
            timeout=20,
        )
        response.raise_for_status()
        for item in response.json():
            candidates.append(
                {
                    "source": "nominatim",
                    "label": item.get("display_name", query),
                    "latitude": float(item.get("lat")),
                    "longitude": float(item.get("lon")),
                }
            )

        return candidates
