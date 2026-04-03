import pytest

from place_finder_ai.models import FindPlaceRequest
from place_finder_ai.providers import ProviderResult
from place_finder_ai.service import PlaceFinderService


class FakeVision:
    async def describe_image(self, image_url: str, prompt: str):
        return [ProviderResult(source="fake", text="park bench trees")]


class FakeGeo:
    async def geocode(self, query: str):
        return [
            {
                "source": "fake_geo",
                "label": f"{query} candidate",
                "latitude": 1.23,
                "longitude": 4.56,
            }
        ]


@pytest.mark.asyncio
async def test_find_places_returns_hints():
    service = PlaceFinderService(FakeVision(), FakeGeo())
    response = await service.find_places(
        FindPlaceRequest(image_url="https://example.com/test.jpg", user_context="old memory")
    )

    assert response.hints
    assert response.hints[0].source == "fake_geo"
