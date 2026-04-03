# Place Finder AI

A starter app that tries to infer where a memory photo was taken by combining **vision APIs** and **map/geocoding APIs**.

## What it does

- Accepts an image URL and optional memory context.
- Calls one or more vision providers (OpenAI Vision, Google Vision if keys exist).
- Builds location seed queries from clues.
- Geocodes seeds using Mapbox (if token exists) and OpenStreetMap Nominatim.
- Returns ranked candidate places.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn place_finder_ai.app:app --reload
```

Then POST to:

```bash
curl -X POST http://127.0.0.1:8000/find-place \
  -H 'content-type: application/json' \
  -d '{
    "image_url": "https://example.com/photo.jpg",
    "user_context": "Photo with my mom in a park, lots of tall trees and benches"
  }'
```

## Optional API keys

Set any of these in your shell (the app auto-detects):

- `OPENAI_API_KEY`
- `GOOGLE_VISION_API_KEY`
- `MAPBOX_TOKEN`

## Notes

This is intentionally a framework you can extend:

- Add reverse image search APIs (SerpAPI / Bing Visual Search / TinEye integration).
- Add OCR providers to detect signs.
- Add EXIF parser pipeline if original image metadata is available.
