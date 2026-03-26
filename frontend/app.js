const authModal = document.getElementById("authModal");
const authForm = document.getElementById("authForm");
const secretInput = document.getElementById("secretInput");
const authStatus = document.getElementById("authStatus");
const changeSecretButton = document.getElementById("changeSecretButton");

const translatorForm = document.getElementById("translatorForm");
const queryInput = document.getElementById("queryInput");
const translateButton = document.getElementById("translateButton");
const promptZone = document.getElementById("promptZone");
const resultMeta = document.getElementById("resultMeta");
const readoutOutput = document.getElementById("readoutOutput");
const sessionTimer = document.getElementById("sessionTimer");

const metaModel = document.getElementById("metaModel");
const metaShift = document.getElementById("metaShift");
const barRecovery = document.getElementById("barRecovery");
const barAbstraction = document.getElementById("barAbstraction");
const barConstraint = document.getElementById("barConstraint");
const constraintTags = document.getElementById("constraintTags");
const diffRaw = document.getElementById("diffRaw");
const diffTranslated = document.getElementById("diffTranslated");

let runtimeSecret = "";
let typeTimer = null;
const sessionStart = Date.now();

function openAuthModal() {
  authModal.setAttribute("aria-hidden", "false");
  secretInput.focus();
}

function closeAuthModal() {
  authModal.setAttribute("aria-hidden", "true");
}

function setAuthStatus(text, armed = false) {
  authStatus.textContent = text;
  authStatus.style.color = armed ? "var(--accent)" : "var(--text-dim)";
}

function setResultMeta(text) {
  resultMeta.textContent = text;
}

function updateSessionTimer() {
  const elapsed = Math.floor((Date.now() - sessionStart) / 1000);
  const hours = String(Math.floor(elapsed / 3600)).padStart(2, "0");
  const minutes = String(Math.floor((elapsed % 3600) / 60)).padStart(2, "0");
  const seconds = String(elapsed % 60).padStart(2, "0");
  sessionTimer.textContent = `${hours}:${minutes}:${seconds}`;
}

function safeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderReadoutSlice(slice, done) {
  if (!slice) {
    readoutOutput.innerHTML = '<span class="readout-idle">No translated signal yet.</span>';
    return;
  }

  const first = safeHtml(slice.charAt(0));
  const middle = safeHtml(slice.slice(1, -1));
  const last = slice.length > 1 ? safeHtml(slice.charAt(slice.length - 1)) : "";

  const firstHtml = `<span class="edge">${first}</span>`;
  const middleHtml = middle;
  const lastHtml = last ? `<span class="edge">${last}</span>` : "";
  const cursor = done ? "" : '<span class="cursor">█</span>';
  const lockClass = done ? "readout-lock" : "";

  readoutOutput.innerHTML = `<span class="readout-content ${lockClass}">${firstHtml}${middleHtml}${lastHtml}${cursor}</span>`;
}

function nextDelay(index, total, char) {
  const progress = total > 0 ? index / total : 1;
  let delay = 12 + Math.abs(progress - 0.5) * 26;

  if (char === "." || char === "!" || char === "?" || char === ";") {
    delay += 42;
  }
  if (progress > 0.9) {
    delay += 30;
  }

  return Math.max(11, Math.round(delay));
}

function typeReadout(text) {
  if (typeTimer) {
    clearTimeout(typeTimer);
    typeTimer = null;
  }

  let index = 0;

  const tick = () => {
    const slice = text.slice(0, index);
    const done = index >= text.length;
    renderReadoutSlice(slice, done);

    if (done) {
      typeTimer = null;
      return;
    }

    const char = text.charAt(index);
    index += 1;
    typeTimer = setTimeout(tick, nextDelay(index, text.length, char));
  };

  tick();
}

function scoreBetween(min, max) {
  return Math.max(min, Math.min(max, Math.round(min + Math.random() * (max - min))));
}

function setBars(values) {
  barRecovery.style.width = `${values.recovery}%`;
  barAbstraction.style.width = `${values.abstraction}%`;
  barConstraint.style.width = `${values.constraint}%`;
}

function tokenSet(text) {
  return new Set(
    text
      .toLowerCase()
      .split(/[^a-z0-9]+/)
      .filter((w) => w.length > 2)
  );
}

function inferTags(original, translated) {
  const tags = ["systems framing", "indirect orbit", "relationship mapping"];

  const o = tokenSet(original);
  const t = tokenSet(translated);
  let overlap = 0;

  o.forEach((w) => {
    if (t.has(w)) overlap += 1;
  });

  if (overlap <= 1) tags.push("lexical divergence");
  if ((translated.match(/[.!?]/g) || []).length <= 3) tags.push("length clamp");
  if (!/how to|what is|can i|explain/i.test(translated)) tags.push("direct ask suppressed");

  return tags.slice(0, 6);
}

function animateTags(tags) {
  constraintTags.innerHTML = "";

  if (!tags.length) {
    constraintTags.innerHTML = '<span class="tag muted">No constraints fired</span>';
    return;
  }

  tags.forEach((tag, idx) => {
    const node = document.createElement("span");
    node.className = "tag";
    node.textContent = tag;
    constraintTags.appendChild(node);

    setTimeout(() => {
      node.classList.add("live");
    }, 40 + idx * 70);
  });
}

function renderDiff(raw, translated) {
  diffRaw.textContent = raw || "-";
  diffTranslated.textContent = translated || "-";

  const rawWords = raw.trim() ? raw.trim().split(/\s+/).length : 0;
  const outWords = translated.trim() ? translated.trim().split(/\s+/).length : 0;
  metaShift.textContent = String(Math.max(0, outWords - rawWords));
}

function triggerInputFlash() {
  promptZone.classList.remove("flash");
  void promptZone.offsetWidth;
  promptZone.classList.add("flash");
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
  setResultMeta("Secret armed in volatile memory.");
  closeAuthModal();
});

queryInput.addEventListener("focus", () => {
  translatorForm.classList.add("focused");
});

queryInput.addEventListener("blur", () => {
  translatorForm.classList.remove("focused");
});

translatorForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!runtimeSecret) {
    setResultMeta("Arm secret before translation.");
    openAuthModal();
    return;
  }

  const query = queryInput.value.trim();
  if (!query) {
    setResultMeta("Give The Machine a query first.");
    return;
  }

  triggerInputFlash();
  translateButton.disabled = true;
  setResultMeta("Running translation circuit...");

  try {
    const response = await fetch("/api/translate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Auth-Secret": runtimeSecret,
      },
      body: JSON.stringify({ query }),
    });

    const data = await response.json().catch(() => ({}));

    if (response.status === 401) {
      runtimeSecret = "";
      setAuthStatus("Secret idle", false);
      setResultMeta("Unauthorized. Re-arm secret.");
      openAuthModal();
      return;
    }

    if (!response.ok) {
      const msg = String(data.error || "translator broke, retry");
      setResultMeta(msg);
      typeReadout(msg);
      renderDiff(query, msg);
      animateTags(["fault state", "provider exception"]);
      setBars({
        recovery: scoreBetween(32, 55),
        abstraction: scoreBetween(8, 26),
        constraint: scoreBetween(24, 44),
      });
      metaModel.textContent = "-";
      return;
    }

    const translated = String(data.translated || "").trim();
    typeReadout(translated);
    renderDiff(String(data.original || query), translated);

    const tags = inferTags(query, translated);
    animateTags(tags);

    setBars({
      recovery: scoreBetween(82, 96),
      abstraction: scoreBetween(74, 94),
      constraint: scoreBetween(80, 97),
    });

    metaModel.textContent = String(data.model || "llama-3.3-70b-versatile");
    setResultMeta("Translation complete.");
  } catch (error) {
    const msg = `Network fault: ${error}`;
    setResultMeta(msg);
    typeReadout(msg);
    animateTags(["network fault"]);
    setBars({ recovery: 15, abstraction: 10, constraint: 18 });
    metaModel.textContent = "-";
  } finally {
    translateButton.disabled = false;
  }
});

updateSessionTimer();
setInterval(updateSessionTimer, 1000);
openAuthModal();
