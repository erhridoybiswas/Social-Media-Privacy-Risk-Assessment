"""
demo_profile.py
===============
A completely FICTIONAL demonstration profile used by the "Load Safe Demo
Profile" button and by the README walkthrough.

This profile belongs to nobody. It contains no real personal data — only
self-reported privacy *settings*, which is exactly the shape of data the
questionnaire collects.

Scenario: a student who has never reviewed their social-media privacy
settings. Deliberately high exposure so that the findings engine,
recommendation engine and improvement simulator all produce meaningful output.
"""

DEMO_PROFILE_LABEL = "Fictional High-Exposure Student Profile (safe demo data)"

DEMO_ANSWERS = {
    # --- A. Profile visibility ---
    "profile_visibility": "PUBLIC",
    "search_engine_visibility": "YES",
    "friends_list_visibility": "PUBLIC",
    "profile_discoverability": "YES",
    "profile_photo_public": "YES",

    # --- B. Personal information ---
    "phone_public": "YES",
    "email_public": "NO",
    "birthday_public": "YES",
    "home_address_public": "NO",
    "workplace_public": "YES",
    "education_public": "YES",
    "relationship_public": "YES",

    # --- C. Location privacy ---
    "location_public": "YES",
    "realtime_location_sharing": "YES",
    "geotagging_enabled": "YES",
    "checkins_public": "YES",
    "travel_posts": "YES",
    "home_work_location_exposed": "YES",

    # --- D. Posts & content ---
    "posts_public": "PUBLIC",
    "stories_public": "PUBLIC",
    "photo_metadata_awareness": "NO",
    "sensitive_docs_in_photos": "SOMETIMES",
    "public_comments_visibility": "PUBLIC",

    # --- E. Connections ---
    "unknown_connections": "YES",
    "connection_verification": "NO",
    "followers_can_message": "YES",
    "blocked_list_awareness": "NO",

    # --- F. Tagging ---
    "anyone_can_tag": "YES",
    "tag_review_enabled": "NO",
    "tagged_posts_auto_appear": "YES",
    "anyone_can_mention": "YES",

    # --- G. Account security ---
    "mfa_enabled": "NO",
    "unique_password": "NOT SURE",
    "password_manager_used": "NO",
    "login_alerts_enabled": "NO",
    "recovery_info_reviewed": "NO",
    "active_sessions_reviewed": "NO",
    "unknown_devices_checked": "NO",

    # --- H. Third-party apps ---
    "third_party_apps_reviewed": "NO",
    "unused_apps_revoked": "NO",
    "social_signin_used": "YES",

    # --- I. Social engineering ---
    "suspicious_link_awareness": "NO",
    "shares_verification_codes": "NO",
    "responds_to_unknown_dms": "SOMETIMES",
    "clicks_unexpected_links": "SOMETIMES",
    "giveaway_participation": "YES",

    # --- J. Digital footprint ---
    "old_posts_reviewed": "NO",
    "privacy_settings_reviewed": "NO",
    "old_unused_accounts": "YES",
    "public_comments_reviewed": "NO",
    "profile_history_awareness": "NO",
}

# Improvements the demo walkthrough applies in the simulator.
DEMO_IMPROVEMENTS = [
    "phone_public",
    "birthday_public",
    "location_public",
    "realtime_location_sharing",
    "travel_posts",
    "checkins_public",
    "geotagging_enabled",
    "unknown_connections",
    "tag_review_enabled",
    "anyone_can_tag",
    "mfa_enabled",
    "login_alerts_enabled",
    "third_party_apps_reviewed",
    "unused_apps_revoked",
    "old_posts_reviewed",
    "privacy_settings_reviewed",
]


def get_demo_profile():
    """Return a copy so callers cannot mutate the module-level constant."""
    return dict(DEMO_ANSWERS)