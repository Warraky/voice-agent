const SAMPLE_TEXT = {
  password:
    "I need help resetting my password and I cannot log in — can you send me a reset link?",
  billing: "There is an unexpected charge on my last invoice and I need a refund review.",
  order: "Can you tell me when my package will be delivered and share the tracking number?",
  outage: "Our dashboard is down and users are getting a 503 error when they try to load reports.",
};

const $ = (id) => document.getElementById(id);

function setLoading(isLoading) {
  $("loading").classList.toggle("hidden", !isLoading);
  $("submit-btn").disabled = isLoading;
}

function showError(message) {
  const el = $("error");
  if (!message) {
    el.classList.add("hidden");
    el.textContent = "";
    return;
  }
  el.textContent = message;
  el.classList.remove("hidden");
}

function showResult(data) {
  $("empty-state").classList.add("hidden");
  $("result-card").classList.remove("hidden");

  $("out-intent").textContent = data.intent;
  $("out-workflow").textContent = data.workflow;
  $("out-action").textContent = data.suggested_action;
  $("out-response").textContent = data.response_text;
  $("out-voice").textContent = data.voice_output;
  $("out-confidence").textContent = `${(data.confidence * 100).toFixed(0)}% (${data.confidence.toFixed(2)})`;

  $("play-btn").disabled = !data.response_text;
  $("play-btn").dataset.text = data.response_text || "";

  const audioEl = $("elevenlabs-audio");
  audioEl.removeAttribute("src");
  audioEl.load();

  const ttsRow = $("tts-status-row");
  const ttsText = $("tts-status-text");
  const ttsDetail = $("tts-status-detail");
  ttsRow.classList.remove("hidden");
  ttsText.textContent = data.tts_status || "skipped";
  if (data.tts_status === "skipped" && !data.tts_detail) {
    ttsDetail.textContent =
      "TTS not requested. Enable the checkbox to call ElevenLabs when credentials are set in the server .env.";
  } else {
    ttsDetail.textContent = data.tts_detail || "";
  }

  const player = $("elevenlabs-player");
  const playerNote = $("elevenlabs-player-note");
  if (data.tts_status === "ok" && data.tts_audio_base64 && data.tts_mime_type) {
    player.classList.remove("hidden");
    playerNote.textContent = "Audio returned inline from ElevenLabs (MP3).";
    audioEl.src = `data:${data.tts_mime_type};base64,${data.tts_audio_base64}`;
  } else {
    player.classList.add("hidden");
    playerNote.textContent = "";
  }
}

async function submitRoute() {
  showError("");
  const message = $("message").value.trim();
  const customerRaw = $("customer-id").value.trim();
  const customer_id = customerRaw.length ? customerRaw : "anonymous";

  if (!message) {
    showError("Enter a support request (simulated transcript).");
    return;
  }

  setLoading(true);
  try {
    const synthesize_speech = $("synthesize-speech").checked;

    const res = await fetch("/route", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ customer_id, message, synthesize_speech }),
    });

    if (!res.ok) {
      const detail = await safeJson(res);
      const msg =
        detail && detail.detail
          ? typeof detail.detail === "string"
            ? detail.detail
            : JSON.stringify(detail.detail)
          : `Request failed (${res.status})`;
      throw new Error(msg);
    }

    const data = await res.json();
    showResult(data);
  } catch (err) {
    showError(err instanceof Error ? err.message : "Something went wrong.");
    $("result-card").classList.add("hidden");
    $("empty-state").classList.remove("hidden");
  } finally {
    setLoading(false);
  }
}

async function safeJson(res) {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

function wireSamples() {
  document.querySelectorAll(".chip[data-sample]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const key = btn.getAttribute("data-sample");
      const text = SAMPLE_TEXT[key];
      if (text) $("message").value = text;
      $("customer-id").value = $("customer-id").value.trim() || "12345";
      $("message").focus();
    });
  });
}

function wirePlay() {
  $("play-btn").addEventListener("click", () => {
    const text = $("play-btn").dataset.text || "";
    if (!text) return;

    if (!window.speechSynthesis) {
      showError("This browser does not expose speech preview. In production, audio would come from your TTS API.");
      return;
    }

    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = 1;
    utter.pitch = 1;
    window.speechSynthesis.speak(utter);
  });
}

$("submit-btn").addEventListener("click", submitRoute);
document.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") submitRoute();
});

wireSamples();
wirePlay();
