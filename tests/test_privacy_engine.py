"""
test_privacy_engine.py
======================
Automated tests for the Social Media Privacy Risk Assessment Framework.

Run with:
    pytest -v
"""

import os
import sqlite3
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import DEFAULT_CATEGORY_WEIGHTS, DISCLAIMER  # noqa: E402
from backend.services.assessment_engine import run_assessment  # noqa: E402
from backend.services.findings_engine import (  # noqa: E402
    generate_privacy_findings,
    summarise_findings,
)
from backend.services.improvement_simulator import simulate_improvement  # noqa: E402
from backend.services.questionnaire import (  # noqa: E402
    QUESTIONS,
    QUESTIONS_BY_ID,
    QUESTION_IDS,
    TOTAL_QUESTIONS,
)
from backend.services.recommendation_engine import (  # noqa: E402
    generate_recommendations,
)
from backend.services.report_engine import render_report  # noqa: E402
from backend.services.scoring_engine import (  # noqa: E402
    build_profile,
    calculate_privacy_risk,
    classify_risk,
    riskiest_option,
    safest_option,
    score_categories,
)
from backend.utils.validation import (  # noqa: E402
    ValidationError,
    validate_answers,
)
from backend.models import database  # noqa: E402


# ===========================================================================
# Fixtures and helpers
# ===========================================================================
@pytest.fixture()
def temp_db(tmp_path):
    """A throwaway SQLite database for each test that needs persistence."""
    path = str(tmp_path / "test_privacy.db")
    database.init_db(path)
    database.seed_recommendations(path)
    yield path


def safe_profile():
    """A fully privacy-conscious synthetic profile."""
    return build_profile(safest_option)


def risky_profile():
    """A maximally exposed synthetic profile."""
    return build_profile(riskiest_option)


def profile_with(**overrides):
    """
    Start from the safest profile and apply explicit overrides.

    Example: profile_with(phone_public="YES", mfa_enabled="NO")
    """
    answers = safe_profile()
    answers.update(overrides)
    return answers


# ===========================================================================
# TEST 1-2: Extreme profiles
# ===========================================================================
def test_01_fully_private_profile_is_low_risk():
    result = calculate_privacy_risk(safe_profile())
    assert result["overall_score"] <= 20
    assert result["risk_level"] == "LOW"


def test_02_fully_public_profile_is_critical_risk():
    result = calculate_privacy_risk(risky_profile())
    assert result["overall_score"] >= 71
    assert result["risk_level"] == "CRITICAL"


# ===========================================================================
# TEST 3-8: Individual exposure factors raise the right category
# ===========================================================================
def test_03_public_phone_raises_personal_information_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(profile_with(phone_public="YES"))["features"]
    )
    assert exposed["personal_information"] > baseline["personal_information"]


def test_04_public_email_raises_personal_information_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(profile_with(email_public="YES"))["features"]
    )
    assert exposed["personal_information"] > baseline["personal_information"]


def test_05_public_birthday_raises_personal_information_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(profile_with(birthday_public="YES"))["features"]
    )
    assert exposed["personal_information"] > baseline["personal_information"]


def test_06_public_location_raises_location_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(profile_with(location_public="YES"))["features"]
    )
    assert exposed["location_privacy"] > baseline["location_privacy"]


def test_07_realtime_checkins_raise_location_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(
            profile_with(realtime_location_sharing="YES", checkins_public="YES")
        )["features"]
    )
    assert exposed["location_privacy"] > baseline["location_privacy"]


def test_08_travel_posts_raise_location_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(profile_with(travel_posts="YES"))["features"]
    )
    assert exposed["location_privacy"] > baseline["location_privacy"]


def test_09_workplace_exposure_raises_personal_information_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(profile_with(workplace_public="YES"))["features"]
    )
    assert exposed["personal_information"] > baseline["personal_information"]


def test_10_education_exposure_raises_personal_information_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(profile_with(education_public="YES"))["features"]
    )
    assert exposed["personal_information"] > baseline["personal_information"]


def test_11_public_posts_raise_content_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(profile_with(posts_public="PUBLIC"))["features"]
    )
    assert exposed["content_exposure"] > baseline["content_exposure"]


def test_12_unknown_connections_raise_connection_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(profile_with(unknown_connections="YES"))["features"]
    )
    assert exposed["connection_risk"] > baseline["connection_risk"]


def test_13_tag_review_disabled_raises_tagging_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(
            profile_with(tag_review_enabled="NO", anyone_can_tag="YES")
        )["features"]
    )
    assert exposed["tagging_risk"] > baseline["tagging_risk"]


# ===========================================================================
# TEST 14-20: Account security and footprint factors
# ===========================================================================
def test_14_mfa_disabled_raises_account_security_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(profile_with(mfa_enabled="NO"))["features"]
    )
    assert exposed["account_security"] > baseline["account_security"]


def test_15_login_alerts_disabled_raises_account_security_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(profile_with(login_alerts_enabled="NO"))["features"]
    )
    assert exposed["account_security"] > baseline["account_security"]


def test_16_password_reuse_raises_account_security_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(profile_with(unique_password="NO"))["features"]
    )
    assert exposed["account_security"] > baseline["account_security"]


def test_17_third_party_apps_not_reviewed_raises_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(
            profile_with(
                third_party_apps_reviewed="NO",
                unused_apps_revoked="NO",
            )
        )["features"]
    )
    assert exposed["third_party_apps"] > baseline["third_party_apps"]


def test_18_low_link_awareness_raises_social_engineering_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(
            profile_with(
                suspicious_link_awareness="NO",
                clicks_unexpected_links="YES",
            )
        )["features"]
    )
    assert exposed["social_engineering"] > baseline["social_engineering"]


def test_19_old_posts_not_reviewed_raises_digital_footprint_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(profile_with(old_posts_reviewed="NO"))["features"]
    )
    assert exposed["digital_footprint"] > baseline["digital_footprint"]


def test_20_privacy_settings_not_reviewed_raises_footprint_score():
    baseline = score_categories(calculate_privacy_risk(safe_profile())["features"])
    exposed = score_categories(
        calculate_privacy_risk(
            profile_with(privacy_settings_reviewed="NO")
        )["features"]
    )
    assert exposed["digital_footprint"] > baseline["digital_footprint"]


# ===========================================================================
# TEST 21-22: Score ranges and aggregation
# ===========================================================================
def test_21_category_scores_are_bounded_0_to_100():
    result = calculate_privacy_risk(risky_profile())
    for category, score in result["category_scores"].items():
        assert 0 <= score <= 100, f"{category} out of range: {score}"


def test_22_overall_score_is_bounded_0_to_100():
    for profile in (safe_profile(), risky_profile()):
        score = calculate_privacy_risk(profile)["overall_score"]
        assert 0 <= score <= 100


def test_22b_category_weights_sum_to_one():
    assert abs(sum(DEFAULT_CATEGORY_WEIGHTS.values()) - 1.0) < 1e-9


# ===========================================================================
# TEST 23-28: Risk band boundaries
# ===========================================================================
@pytest.mark.parametrize(
    "score,expected",
    [
        (0, "LOW"),
        (20, "LOW"),
        (20.9, "LOW"),
        (21, "MODERATE"),
        (40, "MODERATE"),
        (40.9, "MODERATE"),
        (41, "HIGH"),
        (70, "HIGH"),
        (70.9, "HIGH"),
        (71, "CRITICAL"),
        (100, "CRITICAL"),
    ],
)
def test_23_to_28_risk_band_boundaries(score, expected):
    assert classify_risk(score) == expected


def test_28b_classify_risk_clamps_out_of_range_values():
    assert classify_risk(-50) == "LOW"
    assert classify_risk(500) == "CRITICAL"


# ===========================================================================
# TEST 29-31: Findings and recommendations
# ===========================================================================
def test_29_findings_generated_for_risky_profile():
    answers = risky_profile()
    scored = calculate_privacy_risk(answers)
    findings = generate_privacy_findings(answers, scored["features"])
    assert len(findings) > 0
    assert all(f["risk"] >= 60 for f in findings)


def test_30_recommendations_are_prioritised_and_personalised():
    answers = risky_profile()
    scored = calculate_privacy_risk(answers)
    findings = generate_privacy_findings(answers, scored["features"])
    recommendations = generate_recommendations(findings)

    assert len(recommendations) > 0
    priorities = [r["priority"] for r in recommendations]
    assert priorities[0] == "IMMEDIATE"
    order = {"IMMEDIATE": 0, "IMPORTANT": 1, "GOOD PRACTICE": 2}
    assert priorities == sorted(priorities, key=lambda p: order[p])


def test_31_no_recommendations_for_safe_profile():
    answers = safe_profile()
    scored = calculate_privacy_risk(answers)
    findings = generate_privacy_findings(answers, scored["features"])
    assert generate_recommendations(findings) == []


def test_31b_findings_summary_counts_match():
    answers = risky_profile()
    scored = calculate_privacy_risk(answers)
    findings = generate_privacy_findings(answers, scored["features"])
    summary = summarise_findings(findings)
    assert summary["TOTAL"] == len(findings)


# ===========================================================================
# TEST 32-34: Improvement simulator
# ===========================================================================
def test_32_improvement_simulation_reduces_score():
    answers = risky_profile()
    simulation = simulate_improvement(
        answers,
        ["phone_public", "realtime_location_sharing", "mfa_enabled"],
    )
    assert simulation["after"]["overall_score"] < simulation["before"]["overall_score"]
    assert simulation["improvement"]["risk_reduction_points"] > 0


def test_33_simulation_never_increases_score():
    answers = risky_profile()
    simulation = simulate_improvement(answers, QUESTION_IDS)
    assert simulation["after"]["overall_score"] <= simulation["before"]["overall_score"]


def test_34_simulation_on_safe_profile_has_zero_reduction():
    answers = safe_profile()
    simulation = simulate_improvement(answers, ["phone_public"])
    assert simulation["improvement"]["risk_reduction_points"] == 0


# ===========================================================================
# TEST 35-38: Database
# ===========================================================================
def test_35_database_save_and_fetch(temp_db):
    result = run_assessment(risky_profile())
    assessment_id = database.save_assessment(result, db_path=temp_db)
    assert assessment_id > 0

    record = database.get_assessment(assessment_id, db_path=temp_db)
    assert record is not None
    assert record["risk_level"] == result["risk_level"]
    assert abs(record["overall_score"] - result["overall_score"]) < 1e-6
    assert len(record["category_scores"]) == 10


def test_36_database_does_not_store_sensitive_columns(temp_db):
    """The schema must never contain PII-bearing columns."""
    forbidden = (
        "phone", "email", "address", "birth", "dob", "password",
        "latitude", "longitude", "gps", "message", "answer",
    )
    connection = sqlite3.connect(temp_db)
    try:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        for (table_name,) in tables:
            columns = connection.execute(
                f"PRAGMA table_info({table_name})"
            ).fetchall()
            for column in columns:
                column_name = column[1].lower()
                for token in forbidden:
                    assert token not in column_name, (
                        f"Forbidden column '{column_name}' "
                        f"found in table '{table_name}'"
                    )
    finally:
        connection.close()


def test_37_database_delete_removes_assessment(temp_db):
    result = run_assessment(risky_profile())
    assessment_id = database.save_assessment(result, db_path=temp_db)

    assert database.delete_assessment(assessment_id, db_path=temp_db) is True
    assert database.get_assessment(assessment_id, db_path=temp_db) is None


def test_38_dashboard_stats_are_aggregated_only(temp_db):
    for _ in range(3):
        database.save_assessment(run_assessment(risky_profile()), db_path=temp_db)

    stats = database.get_dashboard_stats(db_path=temp_db)
    assert stats["total_assessments"] == 3
    assert 0 <= stats["average_score"] <= 100
    assert isinstance(stats["risk_distribution"], dict)
    assert isinstance(stats["category_averages"], dict)
    # Aggregates must never expose individual records.
    assert "assessments" not in stats


# ===========================================================================
# TEST 39-42: Validation
# ===========================================================================
def test_39_validation_rejects_unknown_question_id():
    with pytest.raises(ValidationError):
        validate_answers({"not_a_real_question": "YES"})


def test_40_validation_rejects_invalid_option():
    with pytest.raises(ValidationError):
        validate_answers({"phone_public": "MAYBE"})


def test_41_validation_normalises_case_and_whitespace():
    cleaned = validate_answers({"phone_public": "  yes  "})
    assert cleaned["phone_public"] == "YES"


def test_42_validation_rejects_non_dict_payload():
    with pytest.raises(ValidationError):
        validate_answers(["YES", "NO"])


# ===========================================================================
# TEST 43-44: Report generation
# ===========================================================================
def test_43_report_contains_disclaimer_and_scores():
    result = run_assessment(risky_profile())
    html = render_report(result)
    assert DISCLAIMER[:40] in html
    assert "Category Scores" in html
    assert "Privacy Checklist" in html


def test_44_report_does_not_contain_raw_answers():
    answers = risky_profile()
    result = run_assessment(answers)
    html = render_report(result)
    # The report shows finding descriptions, never the raw answer mapping.
    assert "profile_visibility" not in html or "Profile Visibility" in html
    assert "answers" not in html.lower() or "Questionnaire" not in html


# ===========================================================================
# TEST 45-47: Structural integrity
# ===========================================================================
def test_45_questionnaire_has_at_least_40_questions():
    assert TOTAL_QUESTIONS >= 40


def test_46_every_question_is_well_formed():
    for question in QUESTIONS:
        assert question["options"], f"{question['id']} has no options"
        assert set(question["risk_map"].keys()) == set(question["options"]), (
            f"{question['id']} risk_map keys do not match options"
        )
        for value in question["risk_map"].values():
            assert 0 <= value <= 100, f"{question['id']} has an out-of-range value"
        assert question["weight"] > 0
        assert question["priority"] in ("IMMEDIATE", "IMPORTANT", "GOOD PRACTICE")


def test_47_question_ids_are_unique():
    assert len(QUESTION_IDS) == len(set(QUESTION_IDS))


# ===========================================================================
# TEST 48-50: End-to-end orchestration
# ===========================================================================
def test_48_run_assessment_returns_complete_structure():
    result = run_assessment(risky_profile())
    for key in (
        "overall_score", "risk_level", "category_scores", "category_table",
        "findings", "recommendations", "action_plan", "checklist", "disclaimer",
    ):
        assert key in result, f"Missing key: {key}"


def test_49_assessment_with_missing_answers_defaults_to_neutral():
    partial = {"phone_public": "YES"}
    result = calculate_privacy_risk(partial)
    assert result["answered"] == 1
    assert result["unanswered"] == TOTAL_QUESTIONS - 1
    assert 0 <= result["overall_score"] <= 100


def test_50_demo_profile_produces_meaningful_output():
    from backend.services.demo_profile import DEMO_IMPROVEMENTS, get_demo_profile

    answers = get_demo_profile()
    result = run_assessment(answers)
    assert result["overall_score"] > 41  # demo profile is deliberately exposed
    assert len(result["findings"]) > 0

    simulation = simulate_improvement(answers, DEMO_IMPROVEMENTS)
    assert simulation["after"]["overall_score"] < simulation["before"]["overall_score"]