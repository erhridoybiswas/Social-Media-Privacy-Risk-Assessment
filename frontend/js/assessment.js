/* ==========================================================================
   assessment.js — questionnaire, results, findings, recommendations, simulator
   ========================================================================== */

let QUESTIONNAIRE = [];        // sections from /api/questionnaire
let ALL_QUESTION_IDS = [];     // flat list of question IDs
let CURRENT_RESULT = null;     // last assessment result
let CATEGORY_CHART = null;     // Chart.js instance

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const data = await API.get("/api/questionnaire");
    QUESTIONNAIRE = data.sections;
    ALL_QUESTION_IDS = QUESTIONNAIRE.flatMap((s) => s.questions.map((q) => q.id));
    renderQuestionnaire(QUESTIONNAIRE);

    // Deep link: /assessment?demo=1 loads the fictional demo profile.
    const params = new URLSearchParams(window.location.search);
    if (params.get("demo") === "1") {
      await loadDemoProfile();
    }
  } catch (error) {
    showError("form-error", error.message);
  }

  document.getElementById("btn-submit").addEventListener("click", submitAssessment);
  document.getElementById("btn-demo").addEventListener("click", loadDemoProfile);
  document.getElementById("btn-reset").addEventListener("click", resetForm);
  document.getElementById("btn-simulate").addEventListener("click", runSimulation);
});

/* ------------------------------------------------------------------ render */
function renderQuestionnaire(sections) {
  const container = document.getElementById("questionnaire");
  container.innerHTML = sections
    .map(
      (section, sectionIndex) => `
      <section class="section-block">
        <div class="section-head">
          <h2>${esc(labelForCategory(section.category))}</h2>
          <span class="count">${section.question_count} questions</span>
        </div>
        ${section.questions
          .map(
            (question) => `
          <div class="question" id="q-${esc(question.id)}">
            <div class="q-text">${esc(question.text)}</div>
            <div class="options">
              ${question.options
                .map(
                  (option) => `
                <label>
                  <input type="radio"
                         name="${esc(question.id)}"
                         value="${esc(option)}"
                         data-qid="${esc(question.id)}">
                  ${esc(option)}
                </label>`
                )
                .join("")}
            </div>
          </div>`
          )
          .join("")}
      </section>
      ${sectionIndex === 0 ? "" : ""}`
    )
    .join("");
}

/* --------------------------------------------------------------- collecting */
function collectAnswers() {
  const answers = {};
  ALL_QUESTION_IDS.forEach((qid) => {
    const selected = document.querySelector(`input[name="${qid}"]:checked`);
    if (selected) answers[qid] = selected.value;
  });
  return answers;
}

function setAnswers(answers) {
  Object.entries(answers).forEach(([qid, value]) => {
    const input = document.querySelector(
      `input[name="${qid}"][value="${CSS.escape(value)}"]`
    );
    if (input) input.checked = true;
  });
}

function resetForm() {
  document.querySelectorAll("input[type=radio]").forEach((input) => {
    input.checked = false;
  });
  document.getElementById("results").classList.add("hidden");
  document.getElementById("form-error").classList.add("hidden");
  CURRENT_RESULT = null;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/* ------------------------------------------------------------------- submit */
async function submitAssessment() {
  const button = document.getElementById("btn-submit");
  const errorBox = document.getElementById("form-error");
  errorBox.classList.add("hidden");

  const answers = collectAnswers();
  const answered = Object.keys(answers).length;

  if (answered < 10) {
    showError(
      "form-error",
      `Please answer at least 10 questions before submitting (answered: ${answered}).`
    );
    return;
  }

  button.disabled = true;
  button.innerHTML = '<span class="spinner"></span>Analysing…';

  try {
    CURRENT_RESULT = await API.post("/api/assessment", { answers, save: true });
    renderResults(CURRENT_RESULT);
    document.getElementById("results").scrollIntoView({ behavior: "smooth" });
  } catch (error) {
    showError("form-error", error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Generate Privacy Risk Score";
  }
}

/* ------------------------------------------------------------------ results */
function renderResults(result) {
  document.getElementById("results").classList.remove("hidden");

  /* --- headline cards --- */
  document.getElementById("score-value").textContent = result.overall_score.toFixed(0);
  document.getElementById("score-value").style.color =
    colourForScore(result.overall_score);

  const badge = document.getElementById("risk-badge");
  badge.textContent = result.risk_level;
  badge.className = `badge ${result.risk_level}`;

  document.getElementById("stat-findings").textContent =
    result.findings_summary.TOTAL;
  document.getElementById("stat-recommendations").textContent =
    result.recommendation_stats.TOTAL;
  document.getElementById("stat-coverage").textContent =
    `${result.answered_count}/${result.answered_count + result.unanswered_count}`;

  const topCategory = result.top_categories[0];
  document.getElementById("stat-top-category").textContent = topCategory
    ? `${topCategory.label} (${topCategory.score.toFixed(0)})`
    : "—";

  /* --- category table --- */
  const rows = Object.entries(result.category_scores)
    .sort((a, b) => b[1] - a[1])
    .map(
      ([category, score]) => `
      <tr>
        <td>${esc(labelForCategory(category))}</td>
        <td class="num">${score.toFixed(1)}</td>
        <td style="width:40%">${scoreBar(score)}</td>
      </tr>`
    )
    .join("");
  document.getElementById("category-table-body").innerHTML = rows;

  /* --- radar chart --- */
  renderCategoryChart(result.category_scores);

  /* --- findings --- */
  const findingsHtml = result.findings.length
    ? result.findings
        .slice(0, 12)
        .map(
          (finding) => `
      <div class="finding ${esc(finding.severity)}">
        <div class="meta">
          ${esc(finding.category_label)} ·
          ${esc(finding.severity)} ·
          risk ${finding.risk.toFixed(0)}
        </div>
        <strong>${esc(finding.description)}</strong>
        <div class="rec">${esc(finding.recommendation)}</div>
      </div>`
        )
        .join("")
    : `<div class="alert info">No findings above the reporting threshold.
       Your reported privacy posture is strong. Continue periodic reviews.</div>`;
  document.getElementById("findings-list").innerHTML = findingsHtml;

  /* --- recommendations --- */
  const recommendationsHtml = result.recommendations.length
    ? result.recommendations
        .slice(0, 15)
        .map(
          (rec) => `
      <div class="finding">
        <div class="meta">
          <span class="pill ${esc(rec.priority.split(" ")[0])}">${esc(rec.priority)}</span>
          ${esc(rec.category_label)}
        </div>
        <strong>${esc(rec.title)}</strong>
        <div class="rec">${esc(rec.recommendation)}</div>
      </div>`
        )
        .join("")
    : `<div class="alert info">No recommendations — reported posture is already strong.</div>`;
  document.getElementById("recommendations-list").innerHTML = recommendationsHtml;

  /* --- simulator checkbox list (top 15 findings by risk) --- */
  const simulatorItems = result.findings
    .slice(0, 15)
    .map(
      (finding) => `
      <label class="options" style="display:flex;margin-bottom:6px">
        <input type="checkbox" class="improve-checkbox"
               value="${esc(finding.finding_id)}" checked>
        ${esc(finding.description)}
      </label>`
    )
    .join("");
  document.getElementById("simulator-options").innerHTML =
    simulatorItems ||
    `<p class="muted">No weaknesses detected to simulate improvements for.</p>`;

  document.getElementById("simulation-output").classList.add("hidden");
}

function renderCategoryChart(categoryScores) {
  const canvas = document.getElementById("category-chart");
  if (!canvas || typeof Chart === "undefined") return;

  const labels = Object.keys(categoryScores).map(labelForCategory);
  const values = Object.values(categoryScores);

  if (CATEGORY_CHART) CATEGORY_CHART.destroy();

  CATEGORY_CHART = new Chart(canvas.getContext("2d"), {
    type: "radar",
    data: {
      labels,
      datasets: [
        {
          label: "Risk (0–100)",
          data: values,
          backgroundColor: "rgba(56,178,172,.22)",
          borderColor: "#38b2ac",
          pointBackgroundColor: "#4fd1c5",
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          min: 0,
          max: 100,
          ticks: { color: "#93a5b8", backdropColor: "transparent", stepSize: 25 },
          grid: { color: "#2a3b4d" },
          angleLines: { color: "#2a3b4d" },
          pointLabels: { color: "#cbd5e0", font: { size: 11 } },
        },
      },
      plugins: { legend: { labels: { color: "#cbd5e0" } } },
    },
  });
}

/* ---------------------------------------------------------------- simulator */
async function runSimulation() {
  if (!CURRENT_RESULT) return;

  const selected = Array.from(
    document.querySelectorAll(".improve-checkbox:checked")
  ).map((input) => input.value);

  if (selected.length === 0) {
    showError("simulation-error", "Select at least one improvement to simulate.");
    return;
  }

  const answers = collectAnswers();
  const button = document.getElementById("btn-simulate");
  button.disabled = true;
  button.innerHTML = '<span class="spinner"></span>Simulating…';

  try {
    const simulation = await API.post("/api/assessment/simulate-improvement", {
      answers,
      apply: selected,
    });

    document.getElementById("simulation-output").classList.remove("hidden");
    document.getElementById("sim-before-score").textContent =
      simulation.before.overall_score.toFixed(0);
    document.getElementById("sim-before-score").style.color =
      colourForScore(simulation.before.overall_score);
    document.getElementById("sim-before-level").textContent = simulation.before.risk_level;
    document.getElementById("sim-before-level").className =
      `badge ${simulation.before.risk_level}`;

    document.getElementById("sim-after-score").textContent =
      simulation.after.overall_score.toFixed(0);
    document.getElementById("sim-after-score").style.color =
      colourForScore(simulation.after.overall_score);
    document.getElementById("sim-after-level").textContent = simulation.after.risk_level;
    document.getElementById("sim-after-level").className =
      `badge ${simulation.after.risk_level}`;

    document.getElementById("sim-reduction").textContent =
      `${simulation.improvement.risk_reduction_points.toFixed(0)} points ` +
      `(${simulation.improvement.risk_reduction_percent.toFixed(1)}%)`;

    document.getElementById("sim-changes").innerHTML = simulation.changed_settings
      .slice(0, 12)
      .map(
        (change) => `
        <li>${esc(change.title)} — <em>${esc(change.from)}</em> →
            <strong>${esc(change.to)}</strong></li>`
      )
      .join("");

    document.getElementById("sim-disclaimer").textContent = simulation.disclaimer;
  } catch (error) {
    showError("simulation-error", error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Simulate Improvements";
  }
}

/* --------------------------------------------------------------- demo data */
async function loadDemoProfile() {
  try {
    const demo = await API.get("/api/demo-profile");
    resetForm();
    setAnswers(demo.answers);
    const notice = document.getElementById("demo-notice");
    notice.classList.remove("hidden");
    notice.innerHTML =
      `<strong>${esc(demo.label)}</strong><br>${esc(demo.note)}`;
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (error) {
    showError("form-error", error.message);
  }
}