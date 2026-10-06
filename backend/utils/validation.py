"""
validation.py
=============
Strict, allow-list-based validation of everything the client sends.

Design goals
------------
* Reject unknown question IDs (prevents parameter pollution / injection).
* Reject answers that are not in the question's declared option set.
* Normalise whitespace and case so "yes" and " YES " behave identically.
* Cap payload size to prevent trivial denial-of-service.
* Never echo raw user input back inside an error message.
"""

from backend.services.questionnaire import QUESTIONS_BY_ID, QUESTION_IDS
from backend.config import CATEGORY_ORDER

MAX_ANSWERS = len(QUESTION_IDS) + 10  # small headroom


class ValidationError(Exception):
    """Raised when the incoming payload fails validation."""


def _clean_string(value, max_length=64):
    if not isinstance(value, str):
        raise ValidationError("Each answer must be a text value.")
    cleaned = value.strip().upper()
    if len(cleaned) > max_length:
        raise ValidationError("An answer value was unexpectedly long.")
    return cleaned


def validate_answers(raw_answers):
    """
    Validate and normalise a mapping of {question_id: answer}.

    Parameters
    ----------
    raw_answers : dict
        The `answers` object from the request JSON.

    Returns
    -------
    dict
        Normalised answers, containing ONLY recognised question IDs.

    Raises
    ------
    ValidationError
        If the payload is malformed, too large, or contains unknown IDs or
        invalid option values.
    """
    if raw_answers is None:
        raise ValidationError("'answers' is required.")
    if not isinstance(raw_answers, dict):
        raise ValidationError("'answers' must be a JSON object.")
    if len(raw_answers) > MAX_ANSWERS:
        raise ValidationError("Too many answers were submitted.")

    clean = {}
    for key, value in raw_answers.items():
        if not isinstance(key, str) or key not in QUESTIONS_BY_ID:
            # Do NOT echo the key back — it may be attacker-controlled content.
            raise ValidationError("The submission contained an unrecognised question.")

        question = QUESTIONS_BY_ID[key]
        answer = _clean_string(value)

        if answer not in question["options"]:
            raise ValidationError(
                f"Invalid option for question '{key}'. "
                f"Allowed values: {', '.join(question['options'])}."
            )
        clean[key] = answer

    return clean


def validate_applied_improvements(raw_ids):
    """
    Validate the list of question IDs the user wants to 'fix' in the
    improvement simulator.
    """
    if raw_ids is None:
        return []
    if not isinstance(raw_ids, list):
        raise ValidationError("'apply' must be a list of question IDs.")
    if len(raw_ids) > MAX_ANSWERS:
        raise ValidationError("Too many improvements were requested.")

    valid = []
    for item in raw_ids:
        if not isinstance(item, str):
            raise ValidationError("Each improvement must be a question ID string.")
        if item not in QUESTIONS_BY_ID:
            raise ValidationError("The submission contained an unrecognised question.")
        valid.append(item)
    return valid


def validate_assessment_id(raw_id):
    """Validate a numeric assessment identifier from the URL."""
    try:
        value = int(raw_id)
    except (TypeError, ValueError):
        raise ValidationError("Assessment ID must be an integer.")
    if value <= 0:
        raise ValidationError("Assessment ID must be a positive integer.")
    return value


def validate_weights(raw_weights):
    """
    Validate optional custom category weights.

    Weights must cover every category, be non-negative, and sum to ~1.0.
    """
    if raw_weights is None:
        return None
    if not isinstance(raw_weights, dict):
        raise ValidationError("'weights' must be a JSON object.")

    clean = {}
    for category in CATEGORY_ORDER:
        if category not in raw_weights:
            raise ValidationError(f"Missing weight for category '{category}'.")
        try:
            value = float(raw_weights[category])
        except (TypeError, ValueError):
            raise ValidationError(f"Weight for '{category}' must be a number.")
        if value < 0 or value > 1:
            raise ValidationError(f"Weight for '{category}' must be between 0 and 1.")
        clean[category] = value

    total = sum(clean.values())
    if abs(total - 1.0) > 0.001:
        raise ValidationError("Category weights must sum to 1.0.")

    return clean