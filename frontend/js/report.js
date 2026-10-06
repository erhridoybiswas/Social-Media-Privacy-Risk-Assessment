/* ==========================================================================
   report.js — generate a full privacy report without persisting anything
   ========================================================================== */

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const data = await API.get("/api/questionnaire");
    renderForm(data.sections);
  } catch (error) {
    showError("report-error", error.message);
  }

  document.getElementById("btn-generate-report")
    .addEventListener("click", generateReport);
  document.getElementById("btn-load-demo")
    .addEventListener("click", loadDemoAnswers);
});

function renderForm(sections) {
  const container = document.getElementById("report-questionnaire");
  container.innerHTML = sections
    .map(
      (section) => `
      <section class="section-block">
        <div class="section-head">
          <h2>${esc(labelForCategory(section.category))}</h2>
          <span class="count">${section.question_count} questions</span>
        </div>
        ${section.questions
          .map(
            (question) => `
          <div class="question">
            <div class="q-text">${esc(question.text)}</div>
            <div class="options">
              ${question.options
                .map(
                  (option) => `
                <label>
                  <input type="radio" name="${esc(question.id)}"
                         value="${esc(option)}">
                  ${esc(option)}
                </label>`
                )
                .join("")}
            </div>
          </div>`
          )
          .join("")}
      </section>`
    )
    .join("");
}

function collectAnswers() {
  const answers = {};
  document.querySelectorAll("input[type=radio]:checked").forEach((input) => {
    answers[input.name] = input.value;
  });
  return answers;
}

async function loadDemoAnswers() {
  const demo = await API.get("/api/demo-profile");
  Object.entries(demo.answers).forEach(([qid, value]) => {
    const input = document.querySelector(
      `input[name="${qid}"][value="${CSS.escape(value)}"]`
    );
    if (input) input.checked = true;
  });
}

async function generateReport() {
  const answers = collectAnswers();
  if (Object.keys(answers).length < 10) {
    showError("report-error", "Please answer at least 10 questions first.");
    return;
  }

  const button = document.getElementById("btn-generate-report");
  button.disabled = true;
  button.innerHTML = '<span class="spinner"></span>Generating…';

  try {
    const response = await fetch("/api/assessment/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answers }),
    });

    if (!response.ok) throw new Error("Report generation failed.");

    const html = await response.text();

    // Render inside an iframe so the report's own styles stay isolated.
    const frame = document.getElementById("report-frame");
    frame.classList.remove("hidden");
    frame.srcdoc = html;

    // Offer a downloadable copy.
    const blob = new Blob([html], { type: "text/html" });
    const link = document.getElementById("download-report");
    link.href = URL.createObjectURL(blob);
    link.download = "privacy-assessment-report.html";
    link.classList.remove("hidden");

    frame.scrollIntoView({ behavior: "smooth" });
  } catch (error) {
    showError("report-error", error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Generate Privacy Report";
  }
}