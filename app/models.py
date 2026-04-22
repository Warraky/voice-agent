from typing import Literal

from pydantic import BaseModel, Field


class RouteRequest(BaseModel):
    """Inbound payload: transcript-shaped text plus customer context."""

    customer_id: str = Field(..., min_length=1, description="Customer identifier from CRM, IAM, or telephony metadata.")
    message: str = Field(..., min_length=1, description="Utterance text (simulated voice transcript or typed fallback).")
    synthesize_speech: bool = Field(
        default=False,
        description="When true, the server may call ElevenLabs TTS using ELEVENLABS_* env vars and return inline audio.",
    )


class RouteResponse(BaseModel):
    """Structured routing outcome for UI, ticketing, or downstream TTS."""

    intent: str
    workflow: str
    suggested_action: str
    response_text: str
    voice_output: str = Field(
        default="placeholder_audio_response.wav",
        description="Token describing audio disposition: placeholder filename, or elevenlabs_inline_audio when TTS succeeded.",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Heuristic match strength from keyword/pattern coverage.")
    tts_status: Literal["skipped", "no_credentials", "ok", "error"] = Field(
        default="skipped",
        description="Whether server-side ElevenLabs synthesis ran for this request.",
    )
    tts_mime_type: str | None = Field(default=None, description="MIME type when tts_audio_base64 is present.")
    tts_audio_base64: str | None = Field(default=None, description="Base64-encoded audio when synthesis succeeded.")
    tts_detail: str | None = Field(default=None, description="Human-readable detail for errors or configuration hints.")
