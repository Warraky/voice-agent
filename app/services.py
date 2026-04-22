"""
Rules-based intent routing with a heuristic confidence score.

Production systems often replace or augment this with a classifier or constrained model;
the structure (intent + workflow + confidence + audit log) stays the same.
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass
from typing import Final, Literal

from app.config import settings
from app.elevenlabs_tts import synthesize_speech
from app.models import RouteRequest, RouteResponse

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IntentDefinition:
    intent: str
    workflow: str
    suggested_action: str
    response_template: str
    keywords: tuple[str, ...]
    patterns: tuple[re.Pattern[str], ...] = ()


# Priority: operational incidents before commerce topics that might co-occur in language.
_INTENT_ORDER: Final[tuple[IntentDefinition, ...]] = (
    IntentDefinition(
        intent="technical_outage",
        workflow="incident_response",
        suggested_action="Create incident ticket and surface status page",
        response_template=(
            "I am sorry you are seeing a service issue. I will log an incident, check our current status, "
            "and share next steps."
        ),
        keywords=("outage", "down", "not working", "503", "500", "error", "crash", "unavailable"),
        patterns=(re.compile(r"\b(is|are)\s+down\b", re.I), re.compile(r"\bservice\s+(issue|problem)\b", re.I)),
    ),
    IntentDefinition(
        intent="password_reset",
        workflow="identity_support",
        suggested_action="Send password reset instructions",
        response_template=(
            "I can help you reset your password. First I will verify your account and then send reset instructions."
        ),
        keywords=(
            "password",
            "reset",
            "forgot password",
            "cannot log in",
            "can't log in",
            "locked out",
            "login",
            "sign in",
        ),
        patterns=(re.compile(r"\blog\s*in\b", re.I),),
    ),
    IntentDefinition(
        intent="billing_issue",
        workflow="billing_disputes",
        suggested_action="Open billing case and pull recent invoices",
        response_template=(
            "I will review your billing profile and recent charges so we can resolve the discrepancy."
        ),
        keywords=("bill", "billing", "invoice", "charge", "charged", "payment", "refund", "subscription", "cost"),
    ),
    IntentDefinition(
        intent="order_status",
        workflow="fulfillment_support",
        suggested_action="Look up order and return tracking or ETA",
        response_template=(
            "Let me pull up your order details and the latest shipping or delivery status."
        ),
        keywords=("order", "shipment", "shipping", "deliver", "delivery", "track", "tracking", "package"),
    ),
)

_DEFAULT: Final[IntentDefinition] = IntentDefinition(
    intent="general_support",
    workflow="triage_queue",
    suggested_action="Route to human agent with transcript",
    response_template="I have captured your request and will connect you with the right specialist.",
    keywords=(),
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _confidence_for_match(norm: str, raw_message: str, definition: IntentDefinition) -> float:
    """
    Map keyword/pattern overlap to a bounded score.

    This is intentionally simple: it demonstrates where a numeric confidence would be
    emitted for guardrails, A/B testing, or human escalation—not a calibrated ML probability.
    """
    keyword_hits = sum(1 for key in definition.keywords if key in norm)
    pattern_hits = sum(1 for pattern in definition.patterns if pattern.search(raw_message))

    if keyword_hits == 0 and pattern_hits == 0:
        return 0.32

    # Stronger overlap nudges confidence upward within a realistic demo band.
    base = 0.56 + 0.09 * keyword_hits + 0.12 * pattern_hits
    return round(min(0.98, base), 2)


def route_message(message: str) -> tuple[IntentDefinition, float]:
    """Return the first matching intent (priority order) and a heuristic confidence."""
    norm = _normalize(message)

    for definition in _INTENT_ORDER:
        keyword_hit = any(key in norm for key in definition.keywords)
        pattern_hit = any(p.search(message) for p in definition.patterns)
        if keyword_hit or pattern_hit:
            return definition, _confidence_for_match(norm, message, definition)

    return _DEFAULT, 0.32


def process_route_request(payload: RouteRequest, correlation_id: str | None = None) -> RouteResponse:
    cid = correlation_id or str(uuid.uuid4())
    match, confidence = route_message(payload.message)

    logger.info(
        "intent_routed",
        extra={
            "correlation_id": cid,
            "customer_id": payload.customer_id,
            "intent": match.intent,
            "workflow": match.workflow,
            "confidence": confidence,
        },
    )

    response_text = match.response_template
    voice_output = "placeholder_audio_response.wav"
    tts_status: Literal["skipped", "no_credentials", "ok", "error"] = "skipped"
    tts_mime_type: str | None = None
    tts_audio_base64: str | None = None
    tts_detail: str | None = None

    if payload.synthesize_speech:
        api_key = (settings.elevenlabs_api_key or "").strip()
        voice_id = (settings.elevenlabs_voice_id or "").strip()
        if not api_key or not voice_id:
            tts_status = "no_credentials"
            tts_detail = "Set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID in the server .env, then restart uvicorn."
        else:
            result = synthesize_speech(
                response_text,
                api_key=api_key,
                voice_id=voice_id,
                model_id=settings.elevenlabs_model_id,
            )
            if result.error:
                tts_status = "error"
                tts_detail = result.error
                logger.warning("elevenlabs_tts_failed", extra={"correlation_id": cid, "detail": result.error[:500]})
            else:
                tts_status = "ok"
                tts_mime_type = result.mime_type
                tts_audio_base64 = result.audio_base64
                voice_output = "elevenlabs_inline_audio"
                approx_bytes = max(0, (len(result.audio_base64) * 3) // 4)
                logger.info("elevenlabs_tts_ok", extra={"correlation_id": cid, "approx_audio_bytes": approx_bytes})

    return RouteResponse(
        intent=match.intent,
        workflow=match.workflow,
        suggested_action=match.suggested_action,
        response_text=response_text,
        voice_output=voice_output,
        confidence=confidence,
        tts_status=tts_status,
        tts_mime_type=tts_mime_type,
        tts_audio_base64=tts_audio_base64,
        tts_detail=tts_detail,
    )
