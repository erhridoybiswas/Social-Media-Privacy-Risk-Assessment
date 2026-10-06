"""
recommendation_engine.py
========================
Turns findings into a deduplicated, prioritised action plan.

Priority bands
--------------
IMMEDIATE      - act today; direct account-takeover or physical-safety impact
IMPORTANT      - act this week; materially reduces exposure
GOOD PRACTICE  - hygiene improvement; do at the next privacy review
"""

from backend.config import PRIORITY_ORDER
from backend.services.questionnaire import QUESTIONS_BY_ID


def generate_recommendations(findings):
    """
    Build a prioritised recommendation list from findings.

    Parameters
    ----------
    findings : list of dict
        Output of generate_privacy_findings().

    Returns
    -------
    list of dict
        {
          recommendation_id, finding_type, risk, title, recommendation,
          priority, severity, category_label
        }
    """
    recommendations = []
    seen = set()

    for finding in findings:
        finding_id = finding["finding_id"]
        if finding_id in seen:
            continue
        seen.add(finding_id)

        question = QUESTIONS_BY_ID.get(finding_id)
        if question is None:
            continue

        recommendations.append({
            "recommendation_id": finding_id,
            "finding_type": finding_id,
            "risk": finding["risk"],
            "title": question["finding"],
            "recommendation": question["recommendation"],
            "priority": question["priority"],
            "severity": finding["severity"],
            "category_label": finding["category_label"],
        })

    recommendations.sort(
        key=lambda r: (PRIORITY_ORDER.get(r["priority"], 9), -r["risk"])
    )
    return recommendations


def prioritised_action_plan(recommendations, limits=None):
    """
    Split recommendations into IMMEDIATE / IMPORTANT / GOOD PRACTICE buckets.

    Parameters
    ----------
    recommendations : list of dict
    limits : dict, optional
        Optional cap per bucket, e.g. {"IMMEDIATE": 5, "IMPORTANT": 5,
        "GOOD PRACTICE": 5}.
    """
    limits = limits or {}
    plan = {"IMMEDIATE": [], "IMPORTANT": [], "GOOD PRACTICE": []}

    for recommendation in recommendations:
        bucket = recommendation["priority"]
        if bucket not in plan:
            continue
        cap = limits.get(bucket)
        if cap is not None and len(plan[bucket]) >= cap:
            continue
        plan[bucket].append(recommendation)

    return plan


def recommendation_stats(recommendations):
    """Counts per priority, used by the dashboard cards."""
    stats = {"IMMEDIATE": 0, "IMPORTANT": 0, "GOOD PRACTICE": 0, "TOTAL": 0}
    for recommendation in recommendations:
        stats[recommendation["priority"]] = stats.get(recommendation["priority"], 0) + 1
        stats["TOTAL"] += 1
    return stats