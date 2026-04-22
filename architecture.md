# Architecture: voice-shaped support routing (with UI)

This document maps the demo to a realistic enterprise voice-support pipeline and calls out what is intentionally out of scope.

## Conceptual pipeline

```text
Channel (phone, web, app)
        │
        ▼
┌──────────────────────┐
│ Request ingestion     │  Audio capture, session metadata, customer identifiers
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Transcript simulation │  ASR / STT (vendor or on-prem) produces text + confidence (ASR-side)
└──────────┬───────────┘
           │  JSON: customer_id + message (this demo’s boundary)
           ▼
┌──────────────────────┐
│ Intent routing        │  Rules, classifier, or constrained LLM → intent + confidence
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Workflow selection    │  Queue / case type / runbook selector (string labels here)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Response generation   │  Templates + facts + policy (short templates in this demo)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Voice synthesis (TTS) │  Optional ElevenLabs MP3 (inline base64 in demo) or placeholder token |
└──────────────────────┘
```

## What ships in this repository

| Concern | Implementation |
|---------|------------------|
| Request ingestion | `POST /route` JSON; browser UI posts the same payload |
| Transcript simulation | Text area + sample chips; no microphone capture |
| Intent routing | Ordered keyword + regex rules in `app/services.py` |
| Workflow selection | `workflow` string per intent |
| Response generation | `response_text` template per intent |
| Confidence | Heuristic from keyword/pattern overlap (not a calibrated model score) |
| TTS | Optional ElevenLabs call (`synthesize_speech` + env); else `voice_output` placeholder; UI can play MP3 or browser preview |
| Observability | `intent_routed` log fields; `x-request-id` middleware |

## Web UI layer

The UI is **static assets + one Jinja template** served by FastAPI. It exists to:

- Make the **JSON contract** legible to stakeholders.
- Show **loading** and **error** states you would expect in a pilot.
- Anchor screenshots for GitHub or a slide deck.

It deliberately avoids a SPA framework to keep maintenance and narrative simple.

## Observability and logging

- Middleware assigns or propagates **`x-request-id`**.
- Routing emits a structured log line including **customer_id**, **intent**, **workflow**, and **confidence**.

In production you would add redaction, sampling, metrics (latency, route distribution), and trace propagation into CRM and TTS calls.

## Enterprise deployment considerations

1. **Gateway**: Authentication, authorization, rate limits, WAF, request size caps.
2. **Data handling**: Minimize PII in logs; encrypt in transit; align with residency requirements.
3. **Configuration**: Externalize intents/thresholds to config or feature flags for ops-owned tuning.
4. **Async boundaries**: Offload slow CRM or ticketing calls to workers; keep the voice path responsive.
5. **Guardrails**: Use confidence and intent-specific policies to drive **human handoff**, not only copy changes.
6. **Multi-tenant**: Separate routing tables and API credentials per tenant where required.

## Where ElevenLabs plugs in

- **ASR / Scribe**: Runs **before** `/route`, producing `message`.
- **TTS**: Runs **after** `response_text` is approved, consuming that string (and voice settings) to produce audio or a stream.

The API shape here is the **stable handoff** between those concerns and your business logic—what solutions engineers typically document in integration guides and security reviews.
