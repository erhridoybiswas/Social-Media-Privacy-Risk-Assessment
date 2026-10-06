"""
improvement_simulator.py
========================
Simulates the effect of remediating selected privacy weaknesses.

For every question the user chooses to "fix", the simulator substitutes the
LOWEST-RISK option from that question's risk_map and re-runs the complete
scoring pipeline.

DISCLAIMER
----------
This is a framework simulation, NOT a guarantee of real-world safety.
The real world contains factors this model does not represent (platform
defaults changing, other people's behaviour, targeted attacks, etc.).
"""

from backend.config import CATEGORY_LABELS, CATEGORY_ORDER
from backend.services.scoring_engine import (
    calculate_privacy_risk,
    safest_option,
)
from backend.services.questionnaire import QUESTIONS_BY_ID
from backend.services.findings_engine import generate_privacy_findings


def simulate_improvement(answers, applied_question_ids, weights=None):
    """
    Compare the current posture against a remediated posture.

    Parameters
    ----------
    answers : dict
        Current normalised answers.
    applied_question_ids : list of str
        Question IDs the user wants to remediate.
    weights : dict, optional
        Custom category weights.

    Returns
    -------
    dict
        before, after, improvement, changed_settings, unchanged_improvements
    """
    current = calculate_privacy_risk(answers, weights)

    improved_answers = dict(answers)
    changed = []
    skipped = []

    for question_id in applied_question_ids:
        question = QUESTIONS_BY_ID.get(question_id)
        if question is None:
            skipped.append({"question_id": question_id, "reason": "unknown question"})
            continue

        best_option = safest_option(question)
        previous_option = improved_answers.get(question_id)

        if previous_option == best_option:
            skipped.append({
                "question_id": question_id,
                "reason": "already at the safest setting",
                "current_value": previous_option,
            })
            continue

        improved_answers[question_id] = best_option
        changed.append({
            "question_id": question_id,
            "title": question["finding"],
            "from": previous_option,
            "to": best_option,
            "category": question["category"],
            "category_label": CATEGORY_LABELS[question["category"]],
            "risk_removed": round(
                current["features"].get(question_id, 0.0)
                - question["risk_map"][best_option],
                2,
            ),
        })

    simulated = calculate_privacy_risk(improved_answers, weights)

    score_before = current["overall_score"]
    score_after = simulated["overall_score"]
    reduction = round(score_before - score_after, 2)

    category_deltas = {}
    for category in CATEGORY_ORDER:
        before_value = current["category_scores"][category]
        after_value = simulated["category_scores"][category]
        category_deltas[category] = {
            "label": CATEGORY_LABELS[category],
            "before": before_value,
            "after": after_value,
            "delta": round(before_value - after_value, 2),
        }

    simulated_findings = generate_privacy_findings(
        improved_answers, simulated["features"]
    )

    return {
        "before": {
            "overall_score": score_before,
            "risk_level": current["risk_level"],
            "category_scores": current["category_scores"],
        },
        "after": {
            "overall_score": score_after,
            "risk_level": simulated["risk_level"],
            "category_scores": simulated["category_scores"],
            "findings_count": len(simulated_findings),
        },
        "improvement": {
            "risk_reduction_points": reduction,
            "risk_reduction_percent": (
                round((reduction / score_before) * 100, 2) if score_before > 0 else 0.0
            ),
            "risk_level_change": f"{current['risk_level']} -> {simulated['risk_level']}",
            "level_improved": simulated["risk_level"] != current["risk_level"],
        },
        "category_deltas": category_deltas,
        "changed_settings": sorted(changed, key=lambda c: -c["risk_removed"]),
        "skipped_improvements": skipped,
        "improved_answers": improved_answers,
        "disclaimer": (
            "Framework simulation only. A lower simulated score does not "
            "guarantee real-world safety; it indicates that the modelled "
            "exposure factors have been reduced."
        ),
    }