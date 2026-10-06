"""
config.py
=========
Central configuration for the Social Media Privacy Risk Assessment Framework.

Everything a reviewer might want to tune (category weights, risk bands,
database location) lives here so the scoring model stays transparent and
auditable.

IMPORTANT
---------
The default weights and thresholds are EDUCATIONAL ASSUMPTIONS.
They must be calibrated against a real risk appetite before being used for
any professional risk decision.
"""

import os

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

DB_PATH = os.environ.get(
    "PRIVACY_DB_PATH",
    os.path.join(DATA_DIR, "privacy_assessment.db"),
)
DATASET_PATH = os.path.join(DATA_DIR, "social_media_privacy_assessments.csv")

# Make sure runtime directories exist.
for _directory in (DATA_DIR, REPORTS_DIR):
    os.makedirs(_directory, exist_ok=True)

# --------------------------------------------------------------------------
# Categories
# --------------------------------------------------------------------------
CATEGORY_ORDER = [
    "profile_visibility",
    "personal_information",
    "location_privacy",
    "content_exposure",
    "connection_risk",
    "tagging_risk",
    "account_security",
    "third_party_apps",
    "social_engineering",
    "digital_footprint",
]

CATEGORY_LABELS = {
    "profile_visibility": "Profile Visibility",
    "personal_information": "Personal Information",
    "location_privacy": "Location Privacy",
    "content_exposure": "Posts & Content",
    "connection_risk": "Connections",
    "tagging_risk": "Tagging & Mentions",
    "account_security": "Account Security",
    "third_party_apps": "Third-Party Apps",
    "social_engineering": "Social Engineering",
    "digital_footprint": "Digital Footprint",
}

# --------------------------------------------------------------------------
# Default category weights (must total 1.00)
# --------------------------------------------------------------------------
DEFAULT_CATEGORY_WEIGHTS = {
    "profile_visibility": 0.10,
    "personal_information": 0.15,
    "location_privacy": 0.15,
    "content_exposure": 0.10,
    "connection_risk": 0.10,
    "tagging_risk": 0.05,
    "account_security": 0.15,
    "third_party_apps": 0.05,
    "social_engineering": 0.10,
    "digital_footprint": 0.05,
}

# --------------------------------------------------------------------------
# Risk bands  (higher score  ==  HIGHER exposure / risk)
# --------------------------------------------------------------------------
RISK_BANDS = [
    (0, 20, "LOW"),
    (21, 40, "MODERATE"),
    (41, 70, "HIGH"),
    (71, 100, "CRITICAL"),
]

RISK_LEVEL_COLORS = {
    "LOW": "#1f9d55",
    "MODERATE": "#d69e2e",
    "HIGH": "#dd6b20",
    "CRITICAL": "#c53030",
}

# Severity thresholds used by the findings engine.
SEVERITY_THRESHOLDS = [
    (90, "CRITICAL"),
    (75, "HIGH"),
    (60, "MEDIUM"),
]
FINDING_THRESHOLD = 60  # only report findings at or above this risk value

# Recommendation priority ordering (for sorting).
PRIORITY_ORDER = {"IMMEDIATE": 0, "IMPORTANT": 1, "GOOD PRACTICE": 2}

# Neutral risk value used when a question is unanswered.
UNKNOWN_RISK = 50.0

# --------------------------------------------------------------------------
# Rate limiting
# --------------------------------------------------------------------------
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60"))

# --------------------------------------------------------------------------
# Persistence toggle (privacy-by-default: saving is explicit)
# --------------------------------------------------------------------------
NO_PERSIST = os.environ.get("PRIVACY_NO_PERSIST", "0") == "1"

# --------------------------------------------------------------------------
# Disclaimer shown in the UI, the API responses and the report
# --------------------------------------------------------------------------
DISCLAIMER = (
    "This assessment is an EDUCATIONAL RISK FRAMEWORK, not a guarantee that an "
    "account will or will not be compromised. Scores are derived from "
    "self-reported privacy practices using configurable, illustrative weights "
    "and thresholds. No real social-media profiles were accessed, scraped, "
    "tracked or profiled. Always validate any risk model against your own "
    "threat model before making professional decisions."
)