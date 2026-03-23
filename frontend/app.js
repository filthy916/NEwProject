const authModal = document.getElementById("auth-modal");
const authInput = document.getElementById("auth-secret");
const authSave = document.getElementById("auth-save");
const unlockButton = document.getElementById("unlock-btn");
const form = document.getElementById("bridge-form");
const submitButton = document.getElementById("submit-btn");
const statusEl = document.getElementById("status");
const results = document.getElementById("results");

const intentEl = document.getElementById("intent");
const providerEl = document.getElementById("result-provider");
const attemptsEl = document.getElementById("attempts");
const finalStatusEl = document.getElementById("final-status");
const refusalEl = document.getElementById("refusal");
const verifiedEl = document.getElementById("verified");
const normalizedEl = document.getElementById("normalized");
const resonantEl = document.getElementById("resonant");
const rawEl = document.getElementById("raw");
const fullJsonEl = document.getElementById("full-json");

let runtimeSecret = "";

function setStatus(message, kind = "") {
  statusEl.textContent = message;
  statusEl.classList.remove("ok", "error");
  if (kind) {
    statusEl.classList.add(kind);
  }
}

function ensureAuthOpen() {
  authModal.classList.add("open");
  authInput.focus();
}

function saveSecret() {
  const value = authInput.value.trim();
  if (!value) {
    setStatus("Auth secret is required before bridge calls.", "error");
    authInput.focus();
    return;
  }
  runtimeSecret = value;
  authModal.classList.remove("open");
  setStatus("Auth secret set in runtime memory only.", "ok");
}

function renderResult(data) {
  results.classList.remove("hidden");
  intentEl.textContent = data.intent || "-";
  providerEl.textContent = data.provider || "-";
  attemptsEl.textContent = String(data.attempts ?? "-");
  finalStatusEl.textContent = data.final_status || "-";
  refusalEl.textContent = String(Boolean(data.refusal_detected));
  verifiedEl.textContent = String(Boolean(data.verified));
  normalizedEl.textContent = data.normalized_input || "";
  resonantEl.textContent = data.resonant_reply || "";
  rawEl.textContent = data.raw_reply || "";
  fullJsonEl.textContent = JSON.stringify(data, null, 2);
}

authSave.addEventListener("click", saveSecret);
unlockButton.addEventListener("click", ensureAuthOpen);
authInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    saveSecret();
  } else if (event.key === "Escape") {
    authModal.classList.remove("open");
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!runtimeSecret) {
    setStatus("Set auth secret before submitting.", "error");
    ensureAuthOpen();
    return;
  }

  const formData = new FormData(form);
  const text = String(formData.get("text") || "").trim();
  if (!text) {
    setStatus("Query payload is required.", "error");
    return;
  }

  const body = {
    direction: String(formData.get("direction") || "human_to_ai"),
    provider: String(formData.get("provider") || "groq"),
    max_retries: Number(formData.get("max_retries") || 3),
    format: String(formData.get("format") || "json"),
    text,
  };

  submitButton.disabled = true;
  setStatus("Bridging query...", "");

  try {
    const response = await fetch("/api/bridge", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Auth-Secret": runtimeSecret,
      },
      body: JSON.stringify(body),
    });

    const payload = await response.json().catch(() => ({}));
    if (response.status === 401) {
      setStatus("Unauthorized. Re-enter auth secret.", "error");
      runtimeSecret = "";
      ensureAuthOpen();
      return;
    }
    if (!response.ok) {
      setStatus(payload.error || "Bridge request failed.", "error");
      return;
    }

    renderResult(payload);
    setStatus("Bridge response received.", "ok");
  } catch (error) {
    setStatus(`Network failure: ${error}`, "error");
  } finally {
    submitButton.disabled = false;
  }
});

ensureAuthOpen();
