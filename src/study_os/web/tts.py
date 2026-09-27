"""Thin TTS helpers: Kokoro OpenAI-compatible proxy (Refs #180)."""

from __future__ import annotations

from typing import Any

import httpx

from .config import Settings


def tts_config_payload(settings: Settings) -> dict[str, Any]:
    engine = settings.tts_engine if settings.tts_engine in {"browser", "kokoro"} else "browser"
    return {
        "engine": engine,
        "voice": settings.kokoro_voice if engine == "kokoro" else None,
        "speed": settings.kokoro_speed if engine == "kokoro" else None,
        "kokoro": engine == "kokoro",
    }


def synthesize_kokoro(settings: Settings, text: str, *, timeout: float = 30.0) -> tuple[bytes, str]:
    """Call Kokoro ``POST /v1/audio/speech``. Returns (audio_bytes, media_type)."""
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("empty_text")
    if len(cleaned) > 4000:
        cleaned = cleaned[:4000]
    url = f"{settings.kokoro_base_url}/v1/audio/speech"
    payload = {
        "model": "kokoro",
        "input": cleaned,
        "voice": settings.kokoro_voice,
        "speed": settings.kokoro_speed,
        "response_format": "mp3",
    }
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        media = resp.headers.get("content-type") or "audio/mpeg"
        return resp.content, media.split(";")[0].strip()
