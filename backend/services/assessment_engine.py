"""
assessment_engine.py
====================
Orchestration layer. Combines scoring, findings and recommendations into the
single result object that the API returns, the database stores (partially),
and the report renders.

This module contains NO Flask and NO SQL — it is pure and unit-testable.
"""

import uuid
from datetime import datetime, timezone

from backend.config import (
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    DISCLAIMER,
    PRIORITY_ORDER,
)
from backend.services.scoring_engine import calculate_privacy_risk
from backend.services.findings_engine import (
    generate_privacy_findings,
    summarise_findings,
)
from backend.services.recommendation_engine import (
    generate_recommendations,
    prioritised_action_plan,
    recommendation_stats,
)
from backend.services.questionnaire import PRIVACY_CHECKLIST


def _assessment_reference():
    """Short, non-guessable reference shown on the report (no PII inside)."""
    return "PRA-" + uuid.uuid4().hex[:10].upper()


def run_assessment(answers, weights=None):
    """
    Execute the complete assessment pipeline.

    Parameters
    ----------
    answers : dict
        Validated {question_id: answer}.
    weights : dict, optional
        Custom category weights (validated elsewhere).

    Returns
    -------
    dict
        A complete, JSON-serialisable assessment result.
    """
    scored = calculate_privacy_risk(answers, weights)
    findings = generate_privacy_findings(answers, scored["features"])
    recommendations = generate_recommendations(findings)

    action_plan = prioritised_action_plan(
        recommendations,
        limits={"IMMEDIATE": 6, "IMPORTANT": 8, "GOOD PRACTICE": 8},
    )

    category_table = [
        {
            "category": category,
            "label": CATEGORY_LABELS[category],
            "score": scored["category_scores"][category],
            "weight": round(scored["weights_used"][category], 4),
        }
        for category in CATEGORY_ORDER
    ]

    return {
        "assessment_reference": _assessment_reference(),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "overall_score": scored["overall_score"],
        "risk_level": scored["risk_level"],
        "category_scores": scored["category_scores"],
        "category_table": category_table,
        "top_categories": scored["top_categories"],
        "coverage": scored["coverage"],
        "answered_count": scored["answered"],
        "unanswered_count": scored["unanswered"],
        "findings": findings,
        "findings_summary": summarise_findings(findings),
        "recommendations": recommendations,
        "recommendation_stats": recommendation_stats(recommendations),
        "action_plan": action_plan,
        "checklist": PRIVACY_CHECKLIST,
        "weights_used": scored["weights_used"],
        "disclaimer": DISCLAIMER,
    }


def top_findings(result, limit=5):
    """Return the N most significant findings, for the report header."""
    return result.get("findings", [])[:limit]


def risk_level_rank(level):
    """Numeric rank for a risk level, useful for comparisons."""
    return {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}.get(level, 0)


def priority_rank(priority):
    """Numeric rank for a recommendation priority."""
    return PRIORITY_ORDER.get(priority, 9)