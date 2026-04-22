"""
Optional call to ElevenLabs Text-to-Speech HTTP API.

Docs: https://elevenlabs.io/docs/api-reference/text-to-speech
"""

from __future__ import annotations

import base64
from typing import NamedTuple

import httpx

ELEVEN_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

# Practical default cap for demo payloads; ElevenLabs supports longer text on paid tiers.
_MAX_TTS_CHARS = 2500


class ElevenLabsTtsResult(NamedTuple):
    mime_type: str
    audio_base64: str
    error: str | None


def synthesize_speech(
    text: str,
    *,
    api_key: str,
    voice_id: str,
    model_id: str,
    timeout_seconds: float = 60.0,
) -> ElevenLabsTtsResult:
    """Return MPEG audio as base64, or an error string suitable for logs/UI."""
    trimmed = (text or "").strip()
    if not trimmed:
        return ElevenLabsTtsResult("", "", "No text to synthesize.")

    if len(trimmed) > _MAX_TTS_CHARS:
        trimmed = trimmed[:_MAX_TTS_CHARS]

    url = ELEVEN_TTS_URL.format(voice_id=voice_id)
    headers = {
        "xi-api-key": api_key,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    body = {"text": trimmed, "model_id": model_id}

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(url, json=body, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        snippet = (exc.response.text or "")[:400]
        return ElevenLabsTtsResult("", "", f"ElevenLabs HTTP {exc.response.status_code}: {snippet}".strip())
    except httpx.RequestError as exc:
        return ElevenLabsTtsResult("", "", f"Request failed: {exc!s}")

    audio = response.content
    if not audio:
        return ElevenLabsTtsResult("", "", "ElevenLabs returned an empty audio body.")

    encoded = base64.standard_b64encode(audio).decode("ascii")
    return ElevenLabsTtsResult("audio/mpeg", encoded, None)
