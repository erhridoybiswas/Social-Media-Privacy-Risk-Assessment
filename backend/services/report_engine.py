"""
report_engine.py
================
Renders a self-contained HTML privacy assessment report.

The report contains ONLY derived scores and finding types. It never contains
raw questionnaire answers, and it never contains PII (the application never
collects any).

The HTML is print-friendly, so "Print -> Save as PDF" produces the PDF export
without adding a PDF dependency.
"""

import html
from datetime import datetime, timezone

from backend.config import (
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    DISCLAIMER,
    RISK_LEVEL_COLORS,
)
from backend.services.assessment_engine import top_findings


def _e(value):
    """HTML-escape any value before inserting it into the document."""
    return html.escape(str(value), quote=True)


def _bar(score, colour):
    """Render a horizontal 0-100 score bar."""
    width = max(0.0, min(100.0, float(score)))
    return (
        f'<div class="bar-track">'
        f'<div class="bar-fill" style="width:{width:.1f}%;background:{colour};"></div>'
        f'</div>'
    )


def render_report(result, assessment_id=None):
    """
    Build the complete HTML report string.

    Parameters
    ----------
    result : dict
        Output of assessment_engine.run_assessment().
    assessment_id : int or None
        Database ID if the assessment was persisted.
    """
    level = result["risk_level"]
    level_colour = RISK_LEVEL_COLORS.get(level, "#4a5568")
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ---- Category table -------------------------------------------------
    category_rows = []
    for row in result["category_table"]:
        colour = _colour_for_score(row["score"])
        category_rows.append(
            "<tr>"
            f"<td>{_e(row['label'])}</td>"
            f"<td class='num'>{row['score']:.1f}</td>"
            f"<td>{_bar(row['score'], colour)}</td>"
            f"<td class='num'>{row['weight'] * 100:.0f}%</td>"
            "</tr>"
        )

    # ---- Findings -------------------------------------------------------
    finding_rows = []
    for index, finding in enumerate(top_findings(result, limit=12), start=1):
        finding_rows.append(
            "<tr>"
            f"<td class='num'>{index}</td>"
            f"<td>{_e(finding['category_label'])}</td>"
            f"<td>{_e(finding['description'])}</td>"
            f"<td><span class='sev sev-{_e(finding['severity'].lower())}'>"
            f"{_e(finding['severity'])}</span></td>"
            f"<td class='num'>{finding['risk']:.0f}</td>"
            "</tr>"
        )
    if not finding_rows:
        finding_rows.append(
            "<tr><td colspan='5' class='muted'>"
            "No findings at or above the reporting threshold. "
            "Continue periodic privacy reviews."
            "</td></tr>"
        )

    # ---- Recommendations -----------------------------------------------
    recommendation_rows = []
    for index, recommendation in enumerate(result["recommendations"][:20], start=1):
        recommendation_rows.append(
            "<tr>"
            f"<td class='num'>{index}</td>"
            f"<td>{_e(recommendation['category_label'])}</td>"
            f"<td>{_e(recommendation['title'])}</td>"
            f"<td>{_e(recommendation['recommendation'])}</td>"
            f"<td><span class='pri pri-{_e(recommendation['priority'].lower().replace(' ', '-'))}'>"
            f"{_e(recommendation['priority'])}</span></td>"
            "</tr>"
        )
    if not recommendation_rows:
        recommendation_rows.append(
            "<tr><td colspan='5' class='muted'>"
            "No recommendations — reported privacy posture is already strong."
            "</td></tr>"
        )

    # ---- Checklist ------------------------------------------------------
    checklist_items = "".join(
        f"<li>&#9744; {_e(item)}</li>" for item in result["checklist"]
    )

    reference = _e(result["assessment_reference"])
    id_line = f" &middot; Record ID {assessment_id}" if assessment_id else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Privacy Assessment Report {reference}</title>
<style>
  :root {{ --ink:#1a202c; --muted:#718096; --line:#e2e8f0; }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: var(--ink); margin: 0; padding: 32px;
    background: #f7fafc; line-height: 1.55;
  }}
  .sheet {{
    max-width: 980px; margin: 0 auto; background: #fff;
    border: 1px solid var(--line); border-radius: 10px; padding: 40px;
  }}
  h1 {{ font-size: 24px; margin: 0 0 4px; }}
  h2 {{ font-size: 16px; margin: 32px 0 12px; text-transform: uppercase;
        letter-spacing: .06em; color: var(--muted); }}
  .meta {{ color: var(--muted); font-size: 13px; }}
  .score-panel {{
    display: flex; flex-wrap: wrap; gap: 24px; align-items: center;
    border: 1px solid var(--line); border-radius: 10px;
    padding: 24px; margin-top: 24px; background: #fbfdff;
  }}
  .score-big {{ font-size: 52px; font-weight: 700; line-height: 1; }}
  .badge {{
    display: inline-block; padding: 6px 14px; border-radius: 999px;
    color: #fff; font-weight: 600; font-size: 13px; letter-spacing: .04em;
  }}
  .metric {{ font-size: 13px; color: var(--muted); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
  th, td {{ text-align: left; padding: 9px 8px; border-bottom: 1px solid var(--line);
            vertical-align: middle; }}
  th {{ font-size: 12px; text-transform: uppercase; letter-spacing: .05em;
        color: var(--muted); }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .bar-track {{ background: #edf2f7; border-radius: 4px; height: 8px; width: 180px; }}
  .bar-fill {{ height: 8px; border-radius: 4px; }}
  .sev, .pri {{ padding: 2px 8px; border-radius: 999px; font-size: 11px;
                font-weight: 700; letter-spacing: .04em; }}
  .sev-critical, .pri-immediate {{ background:#fed7d7; color:#822727; }}
  .sev-high, .pri-important {{ background:#feebc8; color:#7b341e; }}
  .sev-medium {{ background:#fefcbf; color:#744210; }}
  .sev-low, .pri-good-practice {{ background:#e6fffa; color:#234e52; }}
  .muted {{ color: var(--muted); }}
  ul.checklist {{ list-style: none; padding: 0; columns: 2; font-size: 13.5px; }}
  ul.checklist li {{ padding: 4px 0; break-inside: avoid; }}
  .disclaimer {{
    margin-top: 32px; padding: 16px; border-left: 4px solid #d69e2e;
    background: #fffff0; font-size: 13px;
  }}
  @media print {{
    body {{ background:#fff; padding:0; }}
    .sheet {{ border:none; border-radius:0; padding: 0; }}
    h2 {{ page-break-after: avoid; }}
    table {{ page-break-inside: auto; }}
  }}
</style>
</head>
<body>
<div class="sheet">

  <h1>Social Media Privacy Risk Assessment</h1>
  <div class="meta">
    Reference {reference}{id_line}<br>
    Generated {generated}
  </div>

  <div class="score-panel">
    <div>
      <div class="score-big" style="color:{level_colour}">{result['overall_score']:.0f}</div>
      <div class="metric">Overall Privacy Risk (0-100)</div>
    </div>
    <div>
      <span class="badge" style="background:{level_colour}">{_e(level)}</span>
      <div class="metric" style="margin-top:8px">
        Higher score = higher assessed exposure
      </div>
    </div>
    <div>
      <div class="metric">Questions answered</div>
      <div><strong>{result['answered_count']}</strong> /
           {result['answered_count'] + result['unanswered_count']}</div>
    </div>
    <div>
      <div class="metric">Findings</div>
      <div><strong>{result['findings_summary']['TOTAL']}</strong></div>
    </div>
    <div>
      <div class="metric">Recommendations</div>
      <div><strong>{result['recommendation_stats']['TOTAL']}</strong></div>
    </div>
  </div>

  <h2>Category Scores</h2>
  <table>
    <thead>
      <tr><th>Category</th><th class="num">Score</th><th></th><th class="num">Weight</th></tr>
    </thead>
    <tbody>{''.join(category_rows)}</tbody>
  </table>

  <h2>Top Findings</h2>
  <table>
    <thead>
      <tr><th class="num">#</th><th>Category</th><th>Finding</th>
          <th>Severity</th><th class="num">Risk</th></tr>
    </thead>
    <tbody>{''.join(finding_rows)}</tbody>
  </table>

  <h2>Personalised Recommendations</h2>
  <table>
    <thead>
      <tr><th class="num">#</th><th>Category</th><th>Risk</th>
          <th>Recommendation</th><th>Priority</th></tr>
    </thead>
    <tbody>{''.join(recommendation_rows)}</tbody>
  </table>

  <h2>Privacy Checklist</h2>
  <ul class="checklist">{checklist_items}</ul>

  <div class="disclaimer">
    <strong>Disclaimer.</strong> {_e(DISCLAIMER)}
    <br><br>
    This report contains only derived scores and finding categories.
    It does not contain phone numbers, email addresses, home addresses,
    birth dates, passwords, exact locations or private messages — none of
    which are ever collected by this application.
  </div>

</div>
</body>
</html>"""


def _colour_for_score(score):
    """Colour a category score according to its risk band."""
    if score >= 71:
        return RISK_LEVEL_COLORS["CRITICAL"]
    if score >= 41:
        return RISK_LEVEL_COLORS["HIGH"]
    if score >= 21:
        return RISK_LEVEL_COLORS["MODERATE"]
    return RISK_LEVEL_COLORS["LOW"]