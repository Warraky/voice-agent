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
from typing import Final

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

    return RouteResponse(
        intent=match.intent,
        workflow=match.workflow,
        suggested_action=match.suggested_action,
        response_text=match.response_template,
        voice_output="placeholder_audio_response.wav",
        confidence=confidence,
    )
