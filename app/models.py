from pydantic import BaseModel, Field


class RouteRequest(BaseModel):
    """Inbound payload: transcript-shaped text plus customer context."""

    customer_id: str = Field(..., min_length=1, description="Customer identifier from CRM, IAM, or telephony metadata.")
    message: str = Field(..., min_length=1, description="Utterance text (simulated voice transcript or typed fallback).")


class RouteResponse(BaseModel):
    """Structured routing outcome for UI, ticketing, or downstream TTS."""

    intent: str
    workflow: str
    suggested_action: str
    response_text: str
    voice_output: str = Field(
        default="placeholder_audio_response.wav",
        description="Placeholder until a TTS integration returns a URL or stream handle.",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Heuristic match strength from keyword/pattern coverage.")
