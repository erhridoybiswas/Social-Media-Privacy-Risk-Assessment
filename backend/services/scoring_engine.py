"""
scoring_engine.py
=================
The core risk model.

Pipeline
--------
answers  ->  extract_privacy_features()  ->  score_categories()
         ->  calculate_privacy_risk()    ->  classify_risk()

Convention
----------
0   = lower assessed risk / lower exposure
100 = higher assessed risk / higher exposure

IMPORTANT
---------
Weights and thresholds are EDUCATIONAL ASSUMPTIONS (see backend/config.py).
They are configurable so that a reviewer can re-run the model with different
assumptions and compare results.
"""

from backend.config import (
    CATEGORY_ORDER,
    CATEGORY_LABELS,
    DEFAULT_CATEGORY_WEIGHTS,
    RISK_BANDS,
    UNKNOWN_RISK,
)
from backend.services.questionnaire import QUESTIONS, QUESTIONS_BY_ID


# ---------------------------------------------------------------------------
# 1. Feature extraction
# ---------------------------------------------------------------------------
def extract_privacy_features(answers):
    """
    Convert questionnaire responses into numeric privacy-risk features.

    Parameters
    ----------
    answers : dict
        {question_id: answer_string}. Missing or unrecognised answers receive
        the neutral UNKNOWN_RISK value, because "unknown" is itself a risk.

    Returns
    -------
    dict
        {
          "features":      {question_id: risk_value (0-100)},
          "answered":      int,
          "unanswered":    int,
          "coverage":      float,   # fraction of questions answered
          "high_exposure": [question_id, ...]   # features >= 75
        }
    """
    features = {}
    answered = 0

    for question in QUESTIONS:
        qid = question["id"]
        raw_answer = answers.get(qid)

        if raw_answer is None:
            features[qid] = UNKNOWN_RISK
            continue

        risk_value = question["risk_map"].get(raw_answer)
        if risk_value is None:
            # Should be impossible after validation, but never assume.
            features[qid] = UNKNOWN_RISK
        else:
            features[qid] = float(risk_value)
            answered += 1

    total = len(QUESTIONS)
    high_exposure = sorted(
        [qid for qid, value in features.items() if value >= 75],
        key=lambda qid: -features[qid],
    )

    return {
        "features": features,
        "answered": answered,
        "unanswered": total - answered,
        "coverage": round(answered / total, 4) if total else 0.0,
        "high_exposure": high_exposure,
    }


# ---------------------------------------------------------------------------
# 2. Category scoring
# ---------------------------------------------------------------------------
def score_category(category, features):
    """
    Weighted mean of the risk features belonging to one category.

    category_score = sum(risk_i * weight_i) / sum(weight_i)
    """
    questions = [q for q in QUESTIONS if q["category"] == category]
    if not questions:
        return 0.0

    total_weight = sum(q["weight"] for q in questions)
    if total_weight == 0:
        return 0.0

    accumulated = sum(features[q["id"]] * q["weight"] for q in questions)
    return round(accumulated / total_weight, 2)


def score_categories(features):
    """Return {category: score 0-100} for all ten categories."""
    return {category: score_category(category, features) for category in CATEGORY_ORDER}


# ---------------------------------------------------------------------------
# 3. Risk classification
# ---------------------------------------------------------------------------
def classify_risk(score):
    """
    Map a 0-100 risk score to a risk level using the configured bands.

    0-20 LOW | 21-40 MODERATE | 41-70 HIGH | 71-100 CRITICAL
    """
    try:
        value = float(score)
    except (TypeError, ValueError):
        raise ValueError("Risk score must be numeric.")

    value = max(0.0, min(100.0, value))

    for low, high, level in RISK_BANDS:
        if low <= value <= high:
            return level
    return "CRITICAL"


# ---------------------------------------------------------------------------
# 4. Overall risk
# ---------------------------------------------------------------------------
def normalise_weights(weights=None):
    """
    Return a validated weight dict summing to 1.0.

    Falls back to DEFAULT_CATEGORY_WEIGHTS, and re-normalises if the caller
    supplied weights that do not sum exactly to 1.0.
    """
    if not weights:
        return dict(DEFAULT_CATEGORY_WEIGHTS)

    cleaned = {}
    for category in CATEGORY_ORDER:
        cleaned[category] = max(0.0, float(weights.get(category, 0.0)))

    total = sum(cleaned.values())
    if total <= 0:
        return dict(DEFAULT_CATEGORY_WEIGHTS)

    return {category: value / total for category, value in cleaned.items()}


def calculate_privacy_risk(answers, weights=None):
    """
    Full scoring pipeline.

    Returns
    -------
    dict
        overall_score, risk_level, category_scores, category_labels,
        features, coverage, top_categories, weights_used
    """
    extracted = extract_privacy_features(answers)
    features = extracted["features"]

    category_scores = score_categories(features)
    weights_used = normalise_weights(weights)

    overall = sum(
        category_scores[category] * weights_used[category]
        for category in CATEGORY_ORDER
    )
    overall = round(max(0.0, min(100.0, overall)), 2)

    top_categories = sorted(
        category_scores.items(), key=lambda item: -item[1]
    )[:3]

    return {
        "overall_score": overall,
        "risk_level": classify_risk(overall),
        "category_scores": category_scores,
        "category_labels": {c: CATEGORY_LABELS[c] for c in CATEGORY_ORDER},
        "features": features,
        "coverage": extracted["coverage"],
        "answered": extracted["answered"],
        "unanswered": extracted["unanswered"],
        "high_exposure": extracted["high_exposure"],
        "top_categories": [
            {
                "category": category,
                "label": CATEGORY_LABELS[category],
                "score": score,
            }
            for category, score in top_categories
        ],
        "weights_used": weights_used,
    }


# ---------------------------------------------------------------------------
# 5. Convenience helpers used by tests and the simulator
# ---------------------------------------------------------------------------
def safest_option(question):
    """Return the lowest-risk option for a question."""
    return min(question["options"], key=lambda option: question["risk_map"][option])


def riskiest_option(question):
    """Return the highest-risk option for a question."""
    return max(question["options"], key=lambda option: question["risk_map"][option])


def build_profile(option_selector):
    """
    Build a synthetic answer set.

    Parameters
    ----------
    option_selector : callable
        A function taking a question dict and returning one of its options.
        Use safest_option / riskiest_option, or a custom function.

    Returns
    -------
    dict
        {question_id: answer}
    """
    return {q["id"]: option_selector(q) for q in QUESTIONS}