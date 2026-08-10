from __future__ import annotations

import asyncio
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


XAI_IMAGES_URL = "https://api.x.ai/v1/images/generations"


class ImagineError(RuntimeError):
    """A safe, user-facing failure from the image provider."""


def _generate(prompt: str) -> dict[str, str]:
    api_key = os.getenv("XAI_API_KEY", "").strip()
    if not api_key:
        raise ImagineError("Grok Imagine is not configured")

    payload = json.dumps(
        {
            "model": os.getenv("XAI_IMAGE_MODEL", "grok-imagine-image"),
            "prompt": prompt,
            "n": 1,
        }
    ).encode("utf-8")
    request = Request(
        XAI_IMAGES_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "SafarMa-Belink-AI/1.0",
        },
    )
    try:
        with urlopen(request, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        # Provider responses can contain account details; never relay them to clients.
        if exc.code == 429:
            raise ImagineError("Grok Imagine is busy; please retry shortly") from exc
        raise ImagineError("Grok Imagine could not create this image") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ImagineError("Grok Imagine is temporarily unavailable") from exc

    rows = result.get("data") if isinstance(result, dict) else None
    item = rows[0] if isinstance(rows, list) and rows and isinstance(rows[0], dict) else {}
    image_url = str(item.get("url") or "").strip()
    if not image_url.startswith("https://"):
        raise ImagineError("Grok Imagine returned an invalid image")
    revised_prompt = str(item.get("revised_prompt") or prompt).strip()[:2000]
    return {"image_url": image_url, "revised_prompt": revised_prompt}


async def generate_image(prompt: str) -> dict[str, str]:
    return await asyncio.to_thread(_generate, prompt)
