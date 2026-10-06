"""
findings_engine.py
==================
Turns the numeric feature set into human-readable privacy findings.

A finding is produced whenever a question's risk contribution reaches
FINDING_THRESHOLD (default 60). Findings are sorted by severity, then by
risk contribution, then by category weight so the most consequential items
appear first.
"""

from backend.config import (
    CATEGORY_LABELS,
    DEFAULT_CATEGORY_WEIGHTS,
    FINDING_THRESHOLD,
    SEVERITY_THRESHOLDS,
)
from backend.services.questionnaire import QUESTIONS, QUESTIONS_BY_ID


def severity_for(risk_value):
    """Map a risk contribution to a severity label."""
    for threshold, label in SEVERITY_THRESHOLDS:
        if risk_value >= threshold:
            return label
    return "LOW"


def generate_privacy_findings(answers, features, threshold=FINDING_THRESHOLD):
    """
    Produce the list of privacy findings.

    Parameters
    ----------
    answers : dict
        Raw normalised answers (used only to look up what the user selected).
    features : dict
        {question_id: risk_value} produced by the scoring engine.
    threshold : float
        Minimum risk contribution required to raise a finding.

    Returns
    -------
    list of dict
        Each finding: finding_id, category, category_label, finding_type,
        severity, risk, description, recommendation, priority, selected_answer
    """
    findings = []

    for question in QUESTIONS:
        qid = question["id"]
        risk_value = float(features.get(qid, 0.0))

        if risk_value < threshold:
            continue

        findings.append({
            "finding_id": qid,
            "category": question["category"],
            "category_label": CATEGORY_LABELS[question["category"]],
            "finding_type": qid,
            "severity": severity_for(risk_value),
            "risk": risk_value,
            "description": question["finding"],
            "recommendation": question["recommendation"],
            "priority": question["priority"],
            "selected_answer": answers.get(qid, "NOT ANSWERED"),
            "category_weight": DEFAULT_CATEGORY_WEIGHTS.get(question["category"], 0.0),
        })

    severity_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    findings.sort(
        key=lambda f: (
            severity_rank.get(f["severity"], 4),
            -f["risk"],
            -f["category_weight"],
        )
    )
    return findings


def summarise_findings(findings):
    """Return counts per severity for dashboard display."""
    summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for finding in findings:
        summary[finding["severity"]] = summary.get(finding["severity"], 0) + 1
    summary["TOTAL"] = len(findings)
    return summary


def finding_for(finding_id):
    """Look up the source question for a finding ID."""
    return QUESTIONS_BY_ID.get(finding_id)