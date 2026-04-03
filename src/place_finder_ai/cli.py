from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Hint:
    source: str
    label: str
    latitude: float | None
    longitude: float | None
    confidence: float
    reasoning: str


def _is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _to_image_ref(image: str) -> str:
    if _is_url(image):
        return image

    path = Path(image)
    if not path.exists():
        raise FileNotFoundError(f"Image path not found: {image}")

    mime_type, _ = mimetypes.guess_type(str(path))
    mime_type = mime_type or "image/jpeg"
    content = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{content}"


def _extract_seed_queries(text: str) -> list[str]:
    t = text.lower()
    seeds: list[str] = []

    if any(k in t for k in ["park", "bench", "playground"]):
        seeds.append("public park")
    if any(k in t for k in ["lake", "waterfront", "pier"]):
        seeds.append("lake park")
    if any(k in t for k in ["forest", "trail", "eucalyptus", "pine"]):
        seeds.append("forest park")

    for m in re.findall(r"(?:in|near)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})", text):
        seeds.append(m)

    if not seeds:
        seeds.append("family park")
    return list(dict.fromkeys(seeds))


def _openai_visual_clues(image_ref: str, user_context: str) -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return ""

    payload = {
        "model": os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini"),
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Find location clues in this image. "
                            "List concrete clues: vegetation type, architecture, surfaces, signage language, weather, and likely setting. "
                            f"Extra context: {user_context}"
                        ),
                    },
                    {"type": "input_image", "image_url": image_ref},
                ],
            }
        ],
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    output = body.get("output", [])
    snippets: list[str] = []
    for item in output:
        for block in item.get("content", []):
            if block.get("type") in {"output_text", "text"} and block.get("text"):
                snippets.append(block["text"])
    return "\n".join(snippets)


def _nominatim_geocode(query: str) -> list[Hint]:
    params = urllib.parse.urlencode({"q": query, "format": "json", "limit": 3})
    req = urllib.request.Request(
        f"https://nominatim.openstreetmap.org/search?{params}",
        headers={"User-Agent": "place-finder-ai-cli/0.2"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    return [
        Hint(
            source="nominatim",
            label=item.get("display_name", query),
            latitude=float(item["lat"]) if item.get("lat") else None,
            longitude=float(item["lon"]) if item.get("lon") else None,
            confidence=0.35,
            reasoning=f"Geocoded from seed query: {query}",
        )
        for item in data
    ]


def find_places(image: str, context: str) -> dict:
    image_ref = _to_image_ref(image)
    ai_clues = _openai_visual_clues(image_ref, context)
    combined = f"{context}\n{ai_clues}".strip()
    seeds = _extract_seed_queries(combined)

    hints: list[Hint] = []
    for seed in seeds:
        try:
            hints.extend(_nominatim_geocode(seed))
        except Exception as exc:  # noqa: BLE001
            hints.append(Hint("error", seed, None, None, 0.01, f"Geocode failed for '{seed}': {exc}"))

    if not hints:
        hints.append(
            Hint(
                "heuristic",
                "Unknown park",
                None,
                None,
                0.1,
                "No candidates found. Add stronger context like city/country/sign text.",
            )
        )

    return {
        "query_summary": "Used CLI pipeline (OpenAI vision optional + Nominatim geocoding).",
        "seed_queries": seeds,
        "hints": [asdict(h) for h in hints[:10]],
        "used_openai": bool(ai_clues),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Find likely places from a photo and context")
    parser.add_argument("--image", required=True, help="Image URL or local image path")
    parser.add_argument("--context", default="", help="Memory/context clues")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    try:
        result = find_places(args.image, args.context)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n=== Place Finder Results ===")
        print(f"Summary: {result['query_summary']}")
        print(f"Seed queries: {', '.join(result['seed_queries'])}")
        for i, hint in enumerate(result["hints"], start=1):
            print(f"{i}. [{hint['source']}] {hint['label']}")
            print(f"   confidence={hint['confidence']} lat={hint['latitude']} lon={hint['longitude']}")
            print(f"   reason: {hint['reasoning']}")
    return 0
