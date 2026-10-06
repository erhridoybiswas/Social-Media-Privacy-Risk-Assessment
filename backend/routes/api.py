"""
api.py
======
REST API for the Social Media Privacy Risk Assessment Framework.

Endpoints
---------
GET    /api/health
GET    /api/questionnaire
GET    /api/privacy-checklist
GET    /api/demo-profile
POST   /api/assessment
GET    /api/assessment/<id>
GET    /api/assessment/<id>/recommendations
GET    /api/assessment/<id>/report
DELETE /api/assessment/<id>
POST   /api/assessment/simulate-improvement
POST   /api/assessment/simulate-demo
GET    /api/dashboard/stats

Error contract
--------------
400 validation_error | 404 not_found | 429 rate_limited | 500 server_error

No stack traces are ever returned to the client.
"""

from flask import Blueprint, jsonify, request, Response

from backend.config import DISCLAIMER, NO_PERSIST
from backend.services.assessment_engine import run_assessment
from backend.services.demo_profile import (
    DEMO_IMPROVEMENTS,
    DEMO_PROFILE_LABEL,
    get_demo_profile,
)
from backend.services.improvement_simulator import simulate_improvement
from backend.services.questionnaire import (
    PRIVACY_CHECKLIST,
    TOTAL_QUESTIONS,
    public_questionnaire,
)
from backend.services.report_engine import render_report
from backend.models.database import (
    delete_assessment,
    get_assessment,
    get_dashboard_stats,
    get_recommendations_for,
    save_assessment,
)
from backend.utils.rate_limit import rate_limit
from backend.utils.validation import (
    ValidationError,
    validate_answers,
    validate_applied_improvements,
    validate_assessment_id,
    validate_weights,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _json_body():
    """Return the request JSON body, or raise a ValidationError."""
    if not request.is_json:
        raise ValidationError("Request body must be JSON.")
    body = request.get_json(silent=True)
    if body is None or not isinstance(body, dict):
        raise ValidationError("Request body must be a JSON object.")
    return body


def _error(message, status, code):
    return jsonify({"error": code, "message": message}), status


# ---------------------------------------------------------------------------
# Metadata endpoints
# ---------------------------------------------------------------------------
@api_bp.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "social-media-privacy-risk-assessment",
        "total_questions": TOTAL_QUESTIONS,
        "persistence_enabled": not NO_PERSIST,
    })


@api_bp.get("/questionnaire")
def questionnaire():
    """
    Return the full questionnaire structure for rendering.

    Internal risk weights and recommendations are intentionally NOT exposed —
    the scoring model stays server-side.
    """
    return jsonify({
        "total_questions": TOTAL_QUESTIONS,
        "sections": public_questionnaire(),
        "disclaimer": DISCLAIMER,
    })


@api_bp.get("/privacy-checklist")
def privacy_checklist():
    return jsonify({"checklist": PRIVACY_CHECKLIST, "total": len(PRIVACY_CHECKLIST)})


@api_bp.get("/demo-profile")
def demo_profile():
    """A completely fictional, high-exposure profile for safe demonstration."""
    return jsonify({
        "label": DEMO_PROFILE_LABEL,
        "answers": get_demo_profile(),
        "suggested_improvements": DEMO_IMPROVEMENTS,
        "note": (
            "This profile is fictional and contains no real personal data. "
            "It reports privacy SETTINGS only."
        ),
    })


# ---------------------------------------------------------------------------
# Assessment
# ---------------------------------------------------------------------------
@api_bp.post("/assessment")
@rate_limit()
def create_assessment():
    """
    Run a full privacy assessment.

    Body:
        { "answers": {question_id: option, ...},
          "weights": {category: float, ...},   (optional)
          "save":    true|false                (default true) }
    """
    try:
        body = _json_body()
        answers = validate_answers(body.get("answers"))
        weights = validate_weights(body.get("weights"))
        should_save = bool(body.get("save", True))
    except ValidationError as error:
        return _error(str(error), 400, "validation_error")

    result = run_assessment(answers, weights)

    assessment_id = None
    if should_save and not NO_PERSIST:
        try:
            assessment_id = save_assessment(result)
        except Exception:
            # Persistence failure must never break the user's assessment.
            assessment_id = None

    result["assessment_id"] = assessment_id
    result["saved"] = assessment_id is not None
    return jsonify(result), 201


@api_bp.get("/assessment/<int:assessment_id>")
def read_assessment(assessment_id):
    try:
        valid_id = validate_assessment_id(assessment_id)
    except ValidationError as error:
        return _error(str(error), 400, "validation_error")

    record = get_assessment(valid_id)
    if record is None:
        return _error("Assessment not found.", 404, "not_found")

    record["disclaimer"] = DISCLAIMER
    return jsonify(record)


@api_bp.get("/assessment/<int:assessment_id>/recommendations")
def read_recommendations(assessment_id):
    try:
        valid_id = validate_assessment_id(assessment_id)
    except ValidationError as error:
        return _error(str(error), 400, "validation_error")

    if get_assessment(valid_id) is None:
        return _error("Assessment not found.", 404, "not_found")

    return jsonify({"recommendations": get_recommendations_for(valid_id)})


@api_bp.delete("/assessment/<int:assessment_id>")
def remove_assessment(assessment_id):
    """User-controlled deletion (right to erasure)."""
    try:
        valid_id = validate_assessment_id(assessment_id)
    except ValidationError as error:
        return _error(str(error), 400, "validation_error")

    if not delete_assessment(valid_id):
        return _error("Assessment not found.", 404, "not_found")

    return jsonify({"deleted": True, "assessment_id": valid_id})


# ---------------------------------------------------------------------------
# Improvement simulation
# ---------------------------------------------------------------------------
@api_bp.post("/assessment/simulate-improvement")
@rate_limit()
def simulate():
    """
    Body:
        { "answers":   {question_id: option, ...},
          "apply":     [question_id, ...],
          "weights":   {...}  (optional) }
    """
    try:
        body = _json_body()
        answers = validate_answers(body.get("answers"))
        applied = validate_applied_improvements(body.get("apply"))
        weights = validate_weights(body.get("weights"))
    except ValidationError as error:
        return _error(str(error), 400, "validation_error")

    if not applied:
        return _error(
            "Select at least one improvement to simulate.",
            400,
            "validation_error",
        )

    result = simulate_improvement(answers, applied, weights)
    result.pop("improved_answers", None)  # not needed by the client
    return jsonify(result)


@api_bp.post("/assessment/simulate-demo")
@rate_limit()
def simulate_demo():
    """Convenience endpoint: run the fictional demo profile and its fixes."""
    current = run_assessment(get_demo_profile())
    simulation = simulate_improvement(get_demo_profile(), DEMO_IMPROVEMENTS)
    simulation.pop("improved_answers", None)
    return jsonify({
        "label": DEMO_PROFILE_LABEL,
        "assessment": current,
        "simulation": simulation,
    })


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
@api_bp.post("/assessment/report")
@rate_limit()
def report_from_answers():
    """
    Render an HTML report WITHOUT persisting anything.

    This is the privacy-first path: a user can obtain a full report and then
    close the tab, leaving no trace on the server.
    """
    try:
        body = _json_body()
        answers = validate_answers(body.get("answers"))
        weights = validate_weights(body.get("weights"))
    except ValidationError as error:
        return _error(str(error), 400, "validation_error")

    result = run_assessment(answers, weights)
    html_report = render_report(result)
    return Response(html_report, mimetype="text/html")


@api_bp.get("/assessment/<int:assessment_id>/report")
def report_for_assessment(assessment_id):
    """Render an HTML report from a stored (non-sensitive) assessment record."""
    try:
        valid_id = validate_assessment_id(assessment_id)
    except ValidationError as error:
        return _error(str(error), 400, "validation_error")

    record = get_assessment(valid_id)
    if record is None:
        return _error("Assessment not found.", 404, "not_found")

    from backend.config import CATEGORY_LABELS

    # Rebuild a minimal report-ready structure from stored derived data.
    from backend.services.questionnaire import PRIVACY_CHECKLIST

    findings = [
        {
            "category": f["category"],
            "category_label": CATEGORY_LABELS.get(f["category"], f["category"]),
            "description": f["description"],
            "severity": f["severity"],
            "risk": {"CRITICAL": 95, "HIGH": 80, "MEDIUM": 65}.get(f["severity"], 50),
        }
        for f in record["findings"]
    ]

    recommendations = [
        {
            "category_label": "Stored",
            "title": r["finding_type"].replace("_", " ").title(),
            "recommendation": r["recommendation"],
            "priority": r["priority"],
        }
        for r in get_recommendations_for(valid_id)
    ]

    category_table = [
        {
            "category": category,
            "label": CATEGORY_LABELS.get(category, category),
            "score": score,
            "weight": 0.0,
        }
        for category, score in record["category_scores"].items()
    ]

    synthetic_result = {
        "assessment_reference": f"PRA-STORED-{valid_id}",
        "overall_score": record["overall_score"],
        "risk_level": record["risk_level"],
        "category_table": category_table,
        "findings": findings,
        "recommendations": recommendations,
        "checklist": PRIVACY_CHECKLIST,
        "answered_count": TOTAL_QUESTIONS,
        "unanswered_count": 0,
        "findings_summary": {"TOTAL": len(findings)},
        "recommendation_stats": {"TOTAL": len(recommendations)},
    }

    return Response(render_report(synthetic_result, valid_id), mimetype="text/html")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@api_bp.get("/dashboard/stats")
def dashboard_stats():
    """
    Aggregate analytics over stored assessments.

    Returns only aggregated numbers — never individual records or PII.
    """
    stats = get_dashboard_stats()
    stats["disclaimer"] = DISCLAIMER
    stats["note"] = (
        "Aggregates are computed over assessments stored on this instance. "
        "The shipped CSV dataset (data/social_media_privacy_assessments.csv) "
        "is fully synthetic."
    )
    return jsonify(stats)