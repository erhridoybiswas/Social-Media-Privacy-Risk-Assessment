/* ==========================================================================
   api.js — shared helpers used by every page
   ========================================================================== */

const API = {
  async get(path) {
    const response = await fetch(path, { headers: { Accept: "application/json" } });
    return API._handle(response);
  },

  async post(path, body) {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body || {}),
    });
    return API._handle(response);
  },

  async del(path) {
    const response = await fetch(path, { method: "DELETE" });
    return API._handle(response);
  },

  async _handle(response) {
    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json")
      ? await response.json()
      : { message: await response.text() };

    if (!response.ok) {
      const error = new Error(payload.message || `Request failed (${response.status})`);
      error.status = response.status;
      error.payload = payload;
      throw error;
    }
    return payload;
  },
};

/**
 * Escape a value before inserting it into innerHTML.
 * The API already escapes server-side, but defence in depth is cheap.
 */
function esc(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/** Map a risk score to the CSS colour token used across the UI. */
function colourForScore(score) {
  if (score >= 71) return "#c53030";
  if (score >= 41) return "#dd6b20";
  if (score >= 21) return "#d69e2e";
  return "#1f9d55";
}

/** Human-readable category label from a snake_case key. */
function labelForCategory(key) {
  return key
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/** Render a horizontal score bar. */
function scoreBar(score) {
  const value = Math.max(0, Math.min(100, Number(score) || 0));
  return `<div class="bar-track"><div class="bar-fill" style="width:${value}%;
          background:${colourForScore(value)}"></div></div>`;
}

/** Simple toast-style error display. */
function showError(containerId, message) {
  const container = document.getElementById(containerId);
  if (!container) {
    alert(message);
    return;
  }
  container.className = "alert err";
  container.textContent = message;
  container.classList.remove("hidden");
}