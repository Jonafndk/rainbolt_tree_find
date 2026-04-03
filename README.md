# Place Finder AI

You said it "won't let me use it", so this repo now includes **two ways** to run:

1. **No-install CLI (recommended first):** `place_finder_cli.py` (Python stdlib only)
2. **FastAPI server app:** `src/place_finder_ai/app.py` (requires package deps)

---

## Fastest way (no package install)

Run directly with Python:

```bash
python place_finder_cli.py --image /path/to/photo.jpg --context "park with benches and tall trees"
```

Or with an image URL:

```bash
python place_finder_cli.py --image "https://example.com/photo.jpg" --context "photo with my mom in a park" --json
```

### Optional AI boost
If you set `OPENAI_API_KEY`, the CLI sends the image to OpenAI for extra clues before geocoding:

```bash
export OPENAI_API_KEY=your_key_here
python place_finder_cli.py --image /path/to/photo.jpg --context "possible lake nearby"
```

Without a key, it still works using context + Nominatim geocoding.

---

## API server mode (if you want endpoints)

### 1) Install deps

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2) Start server

```bash
uvicorn place_finder_ai.app:app --reload --app-dir src
```

### 3) Test endpoint

```bash
curl -X POST http://127.0.0.1:8000/find-place \
  -H 'content-type: application/json' \
  -d '{
    "image_url": "https://example.com/photo.jpg",
    "user_context": "Photo with my mom in a park, lots of tall trees and benches"
  }'
```

---

## Supported keys (optional)

- `OPENAI_API_KEY`
- `GOOGLE_VISION_API_KEY`
- `MAPBOX_TOKEN`

---

## Troubleshooting

- **"ModuleNotFoundError" in server mode**: install deps with `pip install -e .`.
- **"403" or network errors**: your environment may block outbound calls; test from local machine.
- **No good matches**: add context clues like city, language on signs, season, nearby landmarks.
