# voice-agent-demo

A compact **FastAPI** reference for **voice-shaped enterprise support routing**: ingest a transcript-style utterance, classify it with **transparent rules**, attach a **heuristic confidence**, and return structured fields for CRM, ticketing, or **text-to-speech**. A **small browser UI** (`GET /`) makes the same flow tangible in demos and screenshots.

This is a **portfolio project** meant to reflect how a Solutions Engineer frames **integration boundaries**, **operational follow-through**, and **honest scope**—not a production telephony or voice platform.

## Summary

- **`GET /`**: Presales-friendly demo UI (vanilla HTML/CSS/JS) for entering a simulated transcript and viewing routing output.
- **`POST /route`**: JSON API returning `intent`, `workflow`, `suggested_action`, `response_text`, `voice_output`, `confidence`, and optional **ElevenLabs** fields when `synthesize_speech: true` and server credentials are set.

## Why this matters for voice AI and solutions engineering

Customer voice experiences are **pipelines**: audio capture → transcription → **routing and policy** → systems of record → response generation → **TTS playback**. Vendors and enterprises meet at the seams: stable APIs, observability, guardrails, and phased rollout.

This repository keeps the **middle slice** explicit—the contract after ASR and before TTS—so you can explain how **ElevenLabs** (or another provider) would attach **without** overstating what ships here.

## Demo overview

1. Run the app locally and open the home page.
2. Enter (or sample-paste) a realistic support utterance.
3. Inspect the **result card**: intent, workflow, suggested action, customer-facing response, placeholder audio token, and confidence.
4. Optional: enable **Call ElevenLabs TTS** to synthesize `response_text` on the server (uses your `.env` key; response includes an inline MP3 player when successful).
5. **Browser speech preview** remains available as a separate, non-vendor stub.

## Testing with an ElevenLabs API key

**Security:** put the key only in a server-side `.env` file (never in the browser or in Git). `.gitignore` already excludes `.env`.

1. In the [ElevenLabs API keys](https://elevenlabs.io/app/settings/api-keys) area, create an API key.
2. Copy a **voice ID** from [My Voices](https://elevenlabs.io/app/voice-library) (or use the [List voices API](https://elevenlabs.io/docs/api-reference/voices/search)).
3. In `voice-agent-demo/.env` (create from `.env.example`), set:

```bash
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here
# Optional; default matches app/config.py
# ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

4. Restart `uvicorn` so settings reload.
5. **From the UI:** check **Call ElevenLabs TTS**, submit a route, then use the **ElevenLabs audio** player when `tts_status` is `ok`.

**From curl** (uses quota; response body will be large when audio is included):

```bash
curl -s -X POST http://127.0.0.1:8000/route \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"12345","message":"I need help resetting my password and I cannot log in","synthesize_speech":true}'
```

Response fields:

| Field | Meaning |
|-------|---------|
| `tts_status` | `skipped` \| `no_credentials` \| `ok` \| `error` |
| `tts_mime_type` | e.g. `audio/mpeg` when audio is present |
| `tts_audio_base64` | Base64 MP3 when `tts_status` is `ok` |
| `tts_detail` | Error or configuration hint |

**Note:** This demo returns **inline base64 audio** for simplicity. Production systems usually store audio in object storage and return a **short-lived URL** instead of enlarging JSON payloads.

## Architecture

See **[architecture.md](architecture.md)** for ingestion, routing, workflow selection, response shaping, placeholder TTS, logging, and enterprise scaling notes.

At a glance:

```text
Browser UI ──POST /route──▶ Rules router + confidence ──▶ JSON (+ TTS placeholder)
```

## Why the implementation is intentionally lightweight

- **No ML dependency**: routing is readable keyword/priority logic suitable for interviews and customer conversations about evolution paths.
- **No real-time audio**: avoids SDK complexity while still modeling the **post-transcript** boundary solutions engineers specify in designs.
- **Single service**: enough structure (`app/` modules) to show judgment without mimicking a full platform repo.

## How ElevenLabs fits

- **Upstream**: ASR (for example **ElevenLabs Scribe** or another engine) produces `message` text; your gateway forwards JSON to `/route`.
- **Downstream**: After `response_text` passes policy checks, call **ElevenLabs TTS** and replace `voice_output` with a **URL**, **stream id**, or **signed media reference**.

Keeping routing and TTS **decoupled** is the usual enterprise pattern: swap vendors or share keys per tenant without rewriting business rules.

## Local setup

**Prerequisites:** Python 3.10+.

```bash
cd voice-agent-demo
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # optional
uvicorn app.main:app --reload --port 8000
```

- **UI:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **OpenAPI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Screenshots

_Add 1–2 screenshots of the UI here after you capture them (wide layout + mobile optional)._  
Suggested filenames: `docs/screenshot-desktop.png`, `docs/screenshot-mobile.png`.

## Sample API request and response

```bash
curl -s -X POST http://127.0.0.1:8000/route \
  -H "Content-Type: application/json" \
  -H "x-request-id: demo-trace-001" \
  -d '{"customer_id":"12345","message":"I need help resetting my password and I cannot log in"}'
```

```json
{
  "intent": "password_reset",
  "workflow": "identity_support",
  "suggested_action": "Send password reset instructions",
  "response_text": "I can help you reset your password. First I will verify your account and then send reset instructions.",
  "voice_output": "placeholder_audio_response.wav",
  "confidence": 0.95,
  "tts_status": "skipped",
  "tts_mime_type": null,
  "tts_audio_base64": null,
  "tts_detail": null
}
```

Additional JSON bodies live in **[examples/sample_requests.json](examples/sample_requests.json)**.

## Enterprise considerations

| Topic | Notes |
|-------|--------|
| **Reliability** | Stateless HTTP handler; add retries and circuit breakers around CRM/TTS in real deployments. |
| **Guardrails** | Confidence is heuristic; pair with escalation thresholds, human handoff, and content policies. |
| **Logging** | Structured `intent_routed` log line; `x-request-id` echoed for correlation. |
| **Extensibility** | Replace rules with a service call, feature flags, or hybrid routing without changing the public JSON schema. |

## Future improvements

- Return **signed URLs** to object storage instead of inline base64 for TTS output.
- **Auth** at the edge and per-tenant routing tables.
- **Unit tests** for precedence and confidence monotonicity.
- **Metrics** (latency histograms, intent distribution) exported to your observability stack.

## Portfolio snippets

**GitHub description**

> FastAPI + vanilla UI demo of post-STT support routing: rules-based intent, workflow mapping, heuristic confidence, and a TTS placeholder—scoped for integration and rollout conversations.

**Resume bullet**

> Published **voice-agent-demo**: FastAPI service and minimal web UI that route transcript-style support messages to workflows with heuristic confidence and structured outputs for CRM/ticket/TTS handoff; documents correlation IDs, guardrail thinking, and vendor attachment points.

**Application blurb (short)**

> I built **voice-agent-demo** as a focused integration artifact: it shows how I think about the **post-transcript** contract in voice support, how routing confidence feeds **escalation and QA**, and where **ElevenLabs** (TTS or ASR) would plug in—without claiming this is a full voice stack.

---

_This repository illustrates workflow and integration thinking for customer deployments; it is not a production voice platform._
