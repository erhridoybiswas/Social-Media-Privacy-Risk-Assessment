/* ==========================================================================
   dashboard.js — aggregate privacy analytics (synthetic + stored assessments)
   ========================================================================== */

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const stats = await API.get("/api/dashboard/stats");
    renderCards(stats);
    renderCharts(stats);
    document.getElementById("dash-note").textContent = stats.note || "";
  } catch (error) {
    showError("dash-error", error.message);
  }
});

function renderCards(stats) {
  document.getElementById("card-total").textContent = stats.total_assessments;
  document.getElementById("card-average").textContent =
    stats.average_score ? stats.average_score.toFixed(1) : "—";

  const distribution = stats.risk_distribution || {};
  const criticalHigh =
    (distribution.CRITICAL || 0) + (distribution.HIGH || 0);
  document.getElementById("card-high-risk").textContent = criticalHigh;

  const categoryAverages = stats.category_averages || {};
  const worst = Object.entries(categoryAverages).sort((a, b) => b[1] - a[1])[0];
  document.getElementById("card-worst-category").textContent = worst
    ? `${labelForCategory(worst[0])} (${worst[1].toFixed(0)})`
    : "—";

  document.getElementById("card-weaknesses").textContent =
    (stats.top_weaknesses || []).length;
}

function renderCharts(stats) {
  Chart.defaults.color = "#93a5b8";
  Chart.defaults.borderColor = "#2a3b4d";

  /* ---- 1. Category averages (bar) ---- */
  const categoryAverages = stats.category_averages || {};
  const categoryLabels = Object.keys(categoryAverages).map(labelForCategory);
  const categoryValues = Object.values(categoryAverages);

  new Chart(document.getElementById("chart-categories"), {
    type: "bar",
    data: {
      labels: categoryLabels,
      datasets: [
        {
          label: "Average risk",
          data: categoryValues,
          backgroundColor: categoryValues.map(colourForScore),
          borderRadius: 5,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true, max: 100 } },
      plugins: { legend: { display: false } },
    },
  });

  /* ---- 2. Risk distribution (doughnut) ---- */
  const distribution = stats.risk_distribution || {};
  const levels = ["LOW", "MODERATE", "HIGH", "CRITICAL"];

  new Chart(document.getElementById("chart-distribution"), {
    type: "doughnut",
    data: {
      labels: levels,
      datasets: [
        {
          data: levels.map((level) => distribution[level] || 0),
          backgroundColor: ["#1f9d55", "#d69e2e", "#dd6b20", "#c53030"],
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom" } },
    },
  });

  /* ---- 3. Top weaknesses (horizontal bar) ---- */
  const weaknesses = (stats.top_weaknesses || []).slice(0, 10);
  new Chart(document.getElementById("chart-weaknesses"), {
    type: "bar",
    data: {
      labels: weaknesses.map((item) =>
        item.finding_type.replace(/_/g, " ")
      ),
      datasets: [
        {
          label: "Occurrences",
          data: weaknesses.map((item) => item.count),
          backgroundColor: "#38b2ac",
          borderRadius: 5,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      scales: { x: { beginAtZero: true } },
      plugins: { legend: { display: false } },
    },
  });
}