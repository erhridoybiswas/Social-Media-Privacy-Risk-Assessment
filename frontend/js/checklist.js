/* ==========================================================================
   checklist.js — load and render the printable privacy checklist
   ========================================================================== */

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const data = await API.get("/api/privacy-checklist");
    const list = document.getElementById("checklist");

    list.innerHTML = data.checklist
      .map((item) => `<li>${esc(item)}</li>`)
      .join("");

    const text = [
      "SOCIAL MEDIA PRIVACY CHECKLIST",
      "=".repeat(40),
      "",
      ...data.checklist.map((item) => `[ ] ${item}`),
      "",
      "Educational aid only — not a guarantee of safety.",
    ].join("\n");

    const blob = new Blob([text], { type: "text/plain" });
    document.getElementById("download-checklist").href =
      URL.createObjectURL(blob);
  } catch (error) {
    showError("checklist-error", error.message);
  }
});