const authModal = document.getElementById("authModal");
const authForm = document.getElementById("authForm");
const secretInput = document.getElementById("secretInput");
const authStatus = document.getElementById("authStatus");
const changeSecretButton = document.getElementById("changeSecretButton");
const bridgeForm = document.getElementById("bridgeForm");
const submitButton = document.getElementById("submitButton");
const resultOutput = document.getElementById("resultOutput");
const resultMeta = document.getElementById("resultMeta");
const resultSummary = document.getElementById("resultSummary");
const copyResultButton = document.getElementById("copyResultButton");

let runtimeSecret = "";

function openAuthModal() {
  authModal.setAttribute("aria-hidden", "false");
  secretInput.focus();
}

function closeAuthModal() {
  authModal.setAttribute("aria-hidden", "true");
}

function setAuthStatus(text, armed = false) {
  authStatus.textContent = text;
  authStatus.classList.toggle("armed", armed);
}

function setResultMeta(text) {
  resultMeta.textContent = text;
}

function renderSummary(data) {
  const attempts = Array.isArray(data.attempts) ? data.attempts.length : 0;
  resultSummary.innerHTML = [
    `<p><strong>Status:</strong> ${data.final_status || "unknown"}</p>`,
    `<p><strong>Provider:</strong> ${data.provider || "n/a"}</p>`,
    `<p><strong>Intent:</strong> ${data.intent || "n/a"}</p>`,
    `<p><strong>Attempts:</strong> ${attempts}</p>`,
    `<p><strong>Verified:</strong> ${String(Boolean(data.verified))}</p>`,
  ].join("");
}

async function copyRawResult() {
  if (!resultOutput.textContent) return;
  try {
    await navigator.clipboard.writeText(resultOutput.textContent);
    setResultMeta("Copied raw response to clipboard.");
  } catch {
    setResultMeta("Copy failed.");
  }
}

document.querySelectorAll("[data-close-modal]").forEach((node) => {
  node.addEventListener("click", closeAuthModal);
});

changeSecretButton.addEventListener("click", openAuthModal);

authForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const value = secretInput.value.trim();
  if (!value) {
    setResultMeta("Secret is required.");
    return;
  }
  runtimeSecret = value;
  setAuthStatus("Secret armed", true);
  setResultMeta("Secret stored in memory for this tab only.");
  closeAuthModal();
});

copyResultButton.addEventListener("click", copyRawResult);

bridgeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!runtimeSecret) {
    setResultMeta("Enter secret before dispatch.");
    openAuthModal();
    return;
  }

  const formData = new FormData(bridgeForm);
  const text = String(formData.get("text") || "").trim();
  if (!text) {
    setResultMeta("Instruction is required.");
    return;
  }

  const payload = {
    text,
    direction: String(formData.get("direction") || "human_to_ai"),
    provider: String(formData.get("provider") || "groq"),
    max_retries: Number(formData.get("max_retries") || 3),
    format: String(formData.get("format") || "json"),
  };

  submitButton.disabled = true;
  setResultMeta("Dispatching single-turn bridge request...");

  try {
    const response = await fetch("/api/bridge", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Auth-Secret": runtimeSecret,
      },
      body: JSON.stringify(payload),
    });
    const data = await response.json().catch(() => ({}));

    if (response.status === 401) {
      runtimeSecret = "";
      setAuthStatus("Secret idle", false);
      setResultMeta("Unauthorized. Re-enter secret.");
      openAuthModal();
      return;
    }

    resultOutput.textContent = JSON.stringify(data, null, 2);
    copyResultButton.disabled = false;
    renderSummary(data);

    if (response.ok) {
      setResultMeta("Bridge response received.");
    } else {
      setResultMeta(data.error || "Request failed.");
    }
  } catch (error) {
    setResultMeta(`Network error: ${error}`);
  } finally {
    submitButton.disabled = false;
  }
});

openAuthModal();
