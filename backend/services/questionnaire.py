"""
questionnaire.py
================
Defines the complete 51-question Social Media Privacy Assessment questionnaire
and the printable privacy checklist.

Each question is a dictionary with:

    id             : unique machine-readable key
    category       : one of the ten risk categories
    text           : human-readable question shown to the user
    options        : allowed answers (allow-list used by input validation)
    risk_map       : answer -> exposure/risk contribution
                     (0 = safest, 100 = riskiest)
    weight         : relative importance of the question inside its category
    finding        : short finding description produced when the answer is risky
    recommendation : personalised, defensive recommendation
    priority       : IMMEDIATE | IMPORTANT | GOOD PRACTICE

PRIVACY NOTE
------------
No question asks the user to type a phone number, address, birth date,
password or any other sensitive value. Questions ask only whether such
information is VISIBLE. This allows assessment without collecting the data.
"""

from backend.config import CATEGORY_ORDER  # noqa: F401  (re-exported for convenience)

# ---------------------------------------------------------------------------
# Reusable risk maps
# ---------------------------------------------------------------------------
# "Yes" is the RISKY answer
YES_RISKY = {"YES": 100, "SOMETIMES": 60, "NOT SURE": 50, "NO": 0}
YES_RISKY_3 = {"YES": 100, "NOT SURE": 55, "NO": 0}

# "Yes" is the SAFE answer (user is already doing the right thing)
YES_SAFE = {"YES": 0, "SOMETIMES": 50, "NOT SURE": 55, "NO": 100}
YES_SAFE_3 = {"YES": 0, "NOT SURE": 55, "NO": 100}

# Visibility scopes
VISIBILITY = {"PUBLIC": 100, "FRIENDS": 40, "PRIVATE": 0}

VISIBILITY_OPTIONS = ["PUBLIC", "FRIENDS", "PRIVATE"]
YES_NO_NOTSURE = ["YES", "NO", "NOT SURE"]
YES_NO_SOMETIMES_NOTSURE = ["YES", "NO", "SOMETIMES", "NOT SURE"]


QUESTIONS = [
    # =====================================================================
    # CATEGORY A — PROFILE VISIBILITY
    # =====================================================================
    dict(
        id="profile_visibility",
        category="profile_visibility",
        text="Is your main social-media profile publicly visible?",
        options=VISIBILITY_OPTIONS,
        risk_map=VISIBILITY,
        weight=3,
        finding="Profile is publicly visible to anyone",
        recommendation=(
            "Set your profile visibility to 'Friends only' or 'Private' unless a "
            "public presence is intentional for your work or brand."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="search_engine_visibility",
        category="profile_visibility",
        text="Can your profile be found through search engines (Google, Bing)?",
        options=YES_NO_NOTSURE,
        risk_map=YES_RISKY_3,
        weight=2,
        finding="Profile is discoverable via search engines",
        recommendation=(
            "Disable 'search engine indexing' / 'public search listing' in your "
            "platform's privacy settings."
        ),
        priority="GOOD PRACTICE",
    ),
    dict(
        id="friends_list_visibility",
        category="profile_visibility",
        text="Who can see your friends / followers list?",
        options=VISIBILITY_OPTIONS,
        risk_map=VISIBILITY,
        weight=2,
        finding="Friends / followers list is publicly visible",
        recommendation=(
            "Restrict who can see your friends list. A public social graph is a "
            "common OSINT input used to build trust in impersonation attempts."
        ),
        priority="GOOD PRACTICE",
    ),
    dict(
        id="profile_discoverability",
        category="profile_visibility",
        text="Can people find your profile using your phone number or email address?",
        options=YES_NO_NOTSURE,
        risk_map=YES_RISKY_3,
        weight=2,
        finding="Account is discoverable by phone number or email",
        recommendation=(
            "Turn off 'Let people find me by phone number / email' in the "
            "platform's privacy settings."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="profile_photo_public",
        category="profile_visibility",
        text="Are your profile photo and cover photo visible to everyone?",
        options=YES_NO_NOTSURE,
        risk_map={"YES": 60, "NOT SURE": 45, "NO": 0},
        weight=1,
        finding="Profile and cover photos are publicly visible",
        recommendation=(
            "Limit profile and cover photo visibility to friends if you do not "
            "need a public-facing identity."
        ),
        priority="GOOD PRACTICE",
    ),

    # =====================================================================
    # CATEGORY B — PERSONAL INFORMATION
    # =====================================================================
    dict(
        id="phone_public",
        category="personal_information",
        text="Is your phone number publicly visible on your profile?",
        options=YES_NO_NOTSURE,
        risk_map=YES_RISKY_3,
        weight=3,
        finding="Phone number reported as publicly visible",
        recommendation=(
            "Remove or restrict your phone number to 'Only me'. A public phone "
            "number enables SIM-swap targeting, spam and account-recovery abuse."
        ),
        priority="IMMEDIATE",
    ),
    dict(
        id="email_public",
        category="personal_information",
        text="Is your personal email address publicly visible?",
        options=YES_NO_NOTSURE,
        risk_map={"YES": 85, "NOT SURE": 50, "NO": 0},
        weight=2,
        finding="Personal email address is publicly visible",
        recommendation=(
            "Hide your email address and use a separate address for public or "
            "commercial sign-ups."
        ),
        priority="IMMEDIATE",
    ),
    dict(
        id="birthday_public",
        category="personal_information",
        text="Is your FULL birth date (day, month, year) publicly visible?",
        options=YES_NO_NOTSURE,
        risk_map={"YES": 80, "NOT SURE": 50, "NO": 0},
        weight=3,
        finding="Full birth date is publicly visible",
        recommendation=(
            "Restrict your birth date to 'Only me', or show day/month without the "
            "year. Full birth dates feed identity-verification and 'security "
            "question' abuse."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="home_address_public",
        category="personal_information",
        text="Is any home-related address information publicly visible?",
        options=YES_NO_NOTSURE,
        risk_map={"YES": 100, "NOT SURE": 55, "NO": 0},
        weight=3,
        finding="Home-related address information is exposed",
        recommendation=(
            "Remove any address, locality or housing detail from public view "
            "immediately. This is a physical-safety issue, not only a data issue."
        ),
        priority="IMMEDIATE",
    ),
    dict(
        id="workplace_public",
        category="personal_information",
        text="Is your workplace or employer publicly listed?",
        options=YES_NO_NOTSURE,
        risk_map={"YES": 65, "NOT SURE": 45, "NO": 0},
        weight=1,
        finding="Workplace / employer is publicly listed",
        recommendation=(
            "Consider limiting employer visibility. Employer names are commonly "
            "used to make phishing and pretexting messages believable."
        ),
        priority="GOOD PRACTICE",
    ),
    dict(
        id="education_public",
        category="personal_information",
        text="Is your school, college or university publicly listed?",
        options=YES_NO_NOTSURE,
        risk_map={"YES": 60, "NOT SURE": 45, "NO": 0},
        weight=1,
        finding="Education information is publicly listed",
        recommendation=(
            "Restrict education details to friends if you do not need them "
            "publicly. Campus information is often used in student-targeted scams."
        ),
        priority="GOOD PRACTICE",
    ),
    dict(
        id="relationship_public",
        category="personal_information",
        text="Are your relationship or family details publicly visible?",
        options=YES_NO_NOTSURE,
        risk_map={"YES": 55, "NOT SURE": 45, "NO": 0},
        weight=1,
        finding="Relationship / family details are publicly visible",
        recommendation=(
            "Limit family and relationship information to friends. These details "
            "are frequently used to build believable impersonation stories."
        ),
        priority="GOOD PRACTICE",
    ),

    # =====================================================================
    # CATEGORY C — LOCATION PRIVACY
    # =====================================================================
    dict(
        id="location_public",
        category="location_privacy",
        text="Is your city / general location shown publicly on your profile?",
        options=YES_NO_NOTSURE,
        risk_map={"YES": 75, "NOT SURE": 50, "NO": 0},
        weight=2,
        finding="General location is publicly visible on the profile",
        recommendation=(
            "Remove or restrict your location field. Even a city-level location "
            "narrows targeting significantly."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="realtime_location_sharing",
        category="location_privacy",
        text="Do you share your real-time / live location?",
        options=YES_NO_SOMETIMES_NOTSURE,
        risk_map=YES_RISKY,
        weight=3,
        finding="Real-time location sharing is enabled",
        recommendation=(
            "Stop broadcasting real-time location. Share location only with "
            "specific trusted people through a private channel, and only when "
            "it is genuinely needed."
        ),
        priority="IMMEDIATE",
    ),
    dict(
        id="geotagging_enabled",
        category="location_privacy",
        text="Do you geotag posts or allow automatic location tagging?",
        options=YES_NO_NOTSURE,
        risk_map=YES_RISKY_3,
        weight=2,
        finding="Automatic geotagging is enabled",
        recommendation=(
            "Disable automatic location tagging on posts and stories; add a "
            "location manually only when it is safe and intentional."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="checkins_public",
        category="location_privacy",
        text="Do you publicly check in to places?",
        options=YES_NO_SOMETIMES_NOTSURE,
        risk_map=YES_RISKY,
        weight=2,
        finding="Public check-ins reveal movement patterns",
        recommendation=(
            "Avoid public check-ins, or post them after you have left the "
            "location rather than in real time."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="travel_posts",
        category="location_privacy",
        text="Do you post travel plans before or during a trip?",
        options=YES_NO_SOMETIMES_NOTSURE,
        risk_map=YES_RISKY,
        weight=2,
        finding="Travel plans are posted before or during the trip",
        recommendation=(
            "Post travel content after you return home. Announcing an absence "
            "publicly is a classic burglary and targeting signal."
        ),
        priority="IMMEDIATE",
    ),
    dict(
        id="home_work_location_exposed",
        category="location_privacy",
        text="Could a stranger infer your home or workplace from your posts?",
        options=YES_NO_NOTSURE,
        risk_map=YES_RISKY_3,
        weight=3,
        finding="Home or workplace is inferable from published content",
        recommendation=(
            "Audit recent posts for identifiable buildings, landmarks, uniforms, "
            "badges or repeated routes, and remove or restrict them."
        ),
        priority="IMMEDIATE",
    ),

    # =====================================================================
    # CATEGORY D — POSTS & CONTENT
    # =====================================================================
    dict(
        id="posts_public",
        category="content_exposure",
        text="Who can see your posts by default?",
        options=VISIBILITY_OPTIONS,
        risk_map=VISIBILITY,
        weight=3,
        finding="Default post audience is public",
        recommendation=(
            "Change the default audience for new posts to 'Friends' so that a "
            "moment of inattention does not become a public disclosure."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="stories_public",
        category="content_exposure",
        text="Who can see your stories / status updates?",
        options=VISIBILITY_OPTIONS,
        risk_map=VISIBILITY,
        weight=2,
        finding="Stories / status updates are public",
        recommendation=(
            "Restrict stories to friends and review your 'close friends' list."
        ),
        priority="GOOD PRACTICE",
    ),
    dict(
        id="photo_metadata_awareness",
        category="content_exposure",
        text="Are you aware that photos can carry hidden EXIF / GPS metadata?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=1,
        finding="Low awareness of photo metadata (EXIF) risk",
        recommendation=(
            "Learn how EXIF metadata works and strip metadata before sharing "
            "image files directly (email, cloud links, chat)."
        ),
        priority="GOOD PRACTICE",
    ),
    dict(
        id="sensitive_docs_in_photos",
        category="content_exposure",
        text="Do your photos ever show documents, screens, badges or keys?",
        options=YES_NO_SOMETIMES_NOTSURE,
        risk_map=YES_RISKY,
        weight=3,
        finding="Photos may contain documents, screens or badges",
        recommendation=(
            "Re-check photos before posting. Remove or blur documents, screens, "
            "ID badges, boarding passes and keys."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="public_comments_visibility",
        category="content_exposure",
        text="Who can see the comments you write on public pages?",
        options=VISIBILITY_OPTIONS,
        risk_map=VISIBILITY,
        weight=1,
        finding="Comments on public pages are widely visible",
        recommendation=(
            "Remember that comments are content too — they reveal opinions, "
            "locations and relationships. Restrict where possible."
        ),
        priority="GOOD PRACTICE",
    ),

    # =====================================================================
    # CATEGORY E — FRIENDS / FOLLOWERS
    # =====================================================================
    dict(
        id="unknown_connections",
        category="connection_risk",
        text="Do you accept connection requests from people you do not know?",
        options=YES_NO_SOMETIMES_NOTSURE,
        risk_map=YES_RISKY,
        weight=3,
        finding="Unknown connection requests are frequently accepted",
        recommendation=(
            "Do not accept requests from unfamiliar accounts. Fake profiles are "
            "used to gain access to friends-only content and to build pretexts."
        ),
        priority="IMMEDIATE",
    ),
    dict(
        id="connection_verification",
        category="connection_risk",
        text="Do you verify an unfamiliar profile before accepting a request?",
        options=YES_NO_SOMETIMES_NOTSURE,
        risk_map=YES_SAFE,
        weight=2,
        finding="Unfamiliar profiles are not verified before connecting",
        recommendation=(
            "Before accepting, check mutual connections, account age, posting "
            "history and whether the profile has ever contacted you elsewhere."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="followers_can_message",
        category="connection_risk",
        text="Can anyone (including non-friends) send you direct messages?",
        options=YES_NO_NOTSURE,
        risk_map=YES_RISKY_3,
        weight=2,
        finding="Direct messages are open to non-friends",
        recommendation=(
            "Restrict DMs to people you follow or who follow you; route unknown "
            "messages to a filtered/requests folder."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="blocked_list_awareness",
        category="connection_risk",
        text="Do you periodically review your blocked / restricted list?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=1,
        finding="Blocked / restricted list is not reviewed",
        recommendation=(
            "Review blocked and restricted accounts periodically so that "
            "persistent unwanted contact is not forgotten."
        ),
        priority="GOOD PRACTICE",
    ),

    # =====================================================================
    # CATEGORY F — TAGGING & MENTIONS
    # =====================================================================
    dict(
        id="anyone_can_tag",
        category="tagging_risk",
        text="Can anyone tag you, even if they are not a friend?",
        options=YES_NO_NOTSURE,
        risk_map=YES_RISKY_3,
        weight=3,
        finding="Anyone can tag the account without approval",
        recommendation=(
            "Restrict tagging to friends only, or require manual approval for "
            "every tag."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="tag_review_enabled",
        category="tagging_risk",
        text="Is 'review tags before they appear on your profile' enabled?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=3,
        finding="Tag review is disabled",
        recommendation=(
            "Enable tag review so that tagged content cannot appear on your "
            "profile without your approval."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="tagged_posts_auto_appear",
        category="tagging_risk",
        text="Do posts you are tagged in appear on your profile automatically?",
        options=YES_NO_NOTSURE,
        risk_map=YES_RISKY_3,
        weight=2,
        finding="Tagged posts appear on the profile automatically",
        recommendation=(
            "Turn off automatic display of tagged posts on your timeline."
        ),
        priority="GOOD PRACTICE",
    ),
    dict(
        id="anyone_can_mention",
        category="tagging_risk",
        text="Can unknown accounts mention you in their posts?",
        options=YES_NO_NOTSURE,
        risk_map=YES_RISKY_3,
        weight=2,
        finding="Unknown accounts can mention the account",
        recommendation=(
            "Restrict mentions to people you follow, and review mention "
            "notifications for unwanted attention."
        ),
        priority="GOOD PRACTICE",
    ),

    # =====================================================================
    # CATEGORY G — AUTHENTICATION & ACCOUNT SECURITY
    # =====================================================================
    dict(
        id="mfa_enabled",
        category="account_security",
        text="Is multi-factor authentication (MFA) enabled on this account?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=3,
        finding="MFA is disabled",
        recommendation=(
            "Enable MFA using the strongest method supported: hardware security "
            "key > authenticator app > SMS. SMS is better than nothing but is "
            "vulnerable to SIM-swap attacks."
        ),
        priority="IMMEDIATE",
    ),
    dict(
        id="unique_password",
        category="account_security",
        text="Do you use a password that is unique to this account?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=3,
        finding="Password may be reused across accounts",
        recommendation=(
            "Use a long, unique passphrase for every account. Reused passwords "
            "turn one breach into many compromised accounts (credential stuffing)."
        ),
        priority="IMMEDIATE",
    ),
    dict(
        id="password_manager_used",
        category="account_security",
        text="Do you use a password manager?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=2,
        finding="No password manager in use",
        recommendation=(
            "Adopt a reputable password manager so that unique credentials are "
            "practical to maintain."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="login_alerts_enabled",
        category="account_security",
        text="Are login alerts / new-device alerts enabled?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=2,
        finding="Login alerts are disabled",
        recommendation=(
            "Enable alerts for logins from new devices or locations so that "
            "unauthorised access is detected early."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="recovery_info_reviewed",
        category="account_security",
        text="Have you reviewed your account recovery email/phone recently?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=1,
        finding="Recovery information has not been reviewed",
        recommendation=(
            "Update recovery information and remove outdated phone numbers or "
            "addresses you no longer control."
        ),
        priority="GOOD PRACTICE",
    ),
    dict(
        id="active_sessions_reviewed",
        category="account_security",
        text="Do you review your active sessions / logged-in devices?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=2,
        finding="Active sessions are not reviewed",
        recommendation=(
            "Review active sessions periodically and sign out of anything you "
            "do not recognise."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="unknown_devices_checked",
        category="account_security",
        text="Do you check for unknown devices that are logged in?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=2,
        finding="Unknown logged-in devices are not checked",
        recommendation=(
            "Check the device list after any suspicious activity and remove "
            "unknown devices immediately, then change the password."
        ),
        priority="IMPORTANT",
    ),

    # =====================================================================
    # CATEGORY H — THIRD-PARTY APPS
    # =====================================================================
    dict(
        id="third_party_apps_reviewed",
        category="third_party_apps",
        text="Do you review the third-party applications connected to your account?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=3,
        finding="Connected third-party applications are not reviewed",
        recommendation=(
            "Review connected apps every few months. Each integration is a "
            "standing grant of access to your data."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="unused_apps_revoked",
        category="third_party_apps",
        text="Do you revoke access for apps you no longer use?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=3,
        finding="Unused app permissions are not revoked",
        recommendation=(
            "Apply the Principle of Least Privilege: revoke access for every "
            "app you no longer actively use."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="social_signin_used",
        category="third_party_apps",
        text="Do you use 'Sign in with…' social login on many websites?",
        options=YES_NO_SOMETIMES_NOTSURE,
        risk_map=YES_RISKY,
        weight=2,
        finding="Social login is widely used across third-party sites",
        recommendation=(
            "Review which sites hold social-login access. A compromise of the "
            "social account can cascade to every linked service."
        ),
        priority="GOOD PRACTICE",
    ),

    # =====================================================================
    # CATEGORY I — MESSAGING & SOCIAL ENGINEERING
    # =====================================================================
    dict(
        id="suspicious_link_awareness",
        category="social_engineering",
        text="Can you reliably spot a suspicious link or message?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=2,
        finding="Low confidence in identifying suspicious links/messages",
        recommendation=(
            "Treat urgency, unexpected attachments, shortened links and "
            "credential requests as red flags. Verify through an official "
            "channel before acting."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="shares_verification_codes",
        category="social_engineering",
        text="Have you ever shared an OTP / verification code with anyone?",
        options=YES_NO_SOMETIMES_NOTSURE,
        risk_map=YES_RISKY,
        weight=3,
        finding="Verification codes have been shared",
        recommendation=(
            "Never share one-time codes. No legitimate organisation will ever "
            "ask for them — this is the single most common account-takeover "
            "vector."
        ),
        priority="IMMEDIATE",
    ),
    dict(
        id="responds_to_unknown_dms",
        category="social_engineering",
        text="Do you reply to direct messages from unknown accounts?",
        options=YES_NO_SOMETIMES_NOTSURE,
        risk_map=YES_RISKY,
        weight=2,
        finding="Messages from unknown accounts are answered",
        recommendation=(
            "Do not engage with unsolicited DMs. Engagement confirms an active "
            "account and encourages further targeting."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="clicks_unexpected_links",
        category="social_engineering",
        text="Do you click links that arrive in unexpected messages?",
        options=YES_NO_SOMETIMES_NOTSURE,
        risk_map=YES_RISKY,
        weight=3,
        finding="Links in unexpected messages are clicked",
        recommendation=(
            "Never click links in unsolicited messages. Navigate to the service "
            "manually by typing the address yourself."
        ),
        priority="IMMEDIATE",
    ),
    dict(
        id="giveaway_participation",
        category="social_engineering",
        text="Do you join giveaways/quizzes that ask for personal details?",
        options=YES_NO_SOMETIMES_NOTSURE,
        risk_map=YES_RISKY,
        weight=2,
        finding="Participation in giveaways/quizzes that collect details",
        recommendation=(
            "Avoid 'quizzes' and 'giveaways' that collect personal data — they "
            "are frequently data-harvesting or pretext-building exercises."
        ),
        priority="GOOD PRACTICE",
    ),

    # =====================================================================
    # CATEGORY J — DIGITAL FOOTPRINT
    # =====================================================================
    dict(
        id="old_posts_reviewed",
        category="digital_footprint",
        text="Do you review your old public posts?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=3,
        finding="Old public posts have not been reviewed",
        recommendation=(
            "Review and archive old posts. Content that was harmless years ago "
            "may now reveal a location, employer or relationship."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="privacy_settings_reviewed",
        category="digital_footprint",
        text="Do you review your privacy settings periodically?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=3,
        finding="Privacy settings are not reviewed periodically",
        recommendation=(
            "Schedule a privacy review every 3–6 months, and after any life "
            "change (new job, move, graduation)."
        ),
        priority="IMPORTANT",
    ),
    dict(
        id="old_unused_accounts",
        category="digital_footprint",
        text="Do you have old or unused accounts still online?",
        options=YES_NO_NOTSURE,
        risk_map=YES_RISKY_3,
        weight=2,
        finding="Old or unused accounts remain online",
        recommendation=(
            "Delete or deactivate accounts you no longer use. Dormant accounts "
            "are often forgotten in breach response and still hold your data."
        ),
        priority="GOOD PRACTICE",
    ),
    dict(
        id="public_comments_reviewed",
        category="digital_footprint",
        text="Do you review your old public comments?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=1,
        finding="Old public comments have not been reviewed",
        recommendation=(
            "Review old comments — they reveal opinions, locations and "
            "associations, and they are indexed by search engines."
        ),
        priority="GOOD PRACTICE",
    ),
    dict(
        id="profile_history_awareness",
        category="digital_footprint",
        text="Are you aware of what your profile looked like several years ago?",
        options=YES_NO_NOTSURE,
        risk_map=YES_SAFE_3,
        weight=1,
        finding="Profile history is not known",
        recommendation=(
            "Check archived versions of your profile and old screenshots to "
            "understand your historical exposure."
        ),
        priority="GOOD PRACTICE",
    ),
]


# ---------------------------------------------------------------------------
# Convenience lookups
# ---------------------------------------------------------------------------
QUESTIONS_BY_ID = {q["id"]: q for q in QUESTIONS}
QUESTION_IDS = [q["id"] for q in QUESTIONS]
TOTAL_QUESTIONS = len(QUESTIONS)


def questions_by_category():
    """Return {category: [question, ...]} preserving CATEGORY_ORDER."""
    grouped = {category: [] for category in CATEGORY_ORDER}
    for question in QUESTIONS:
        grouped.setdefault(question["category"], []).append(question)
    return grouped


def public_questionnaire():
    """
    Return a serialisable copy of the questionnaire WITHOUT the internal
    risk_map, finding and recommendation data.

    Rationale: the client only needs to render the form. Keeping the scoring
    model server-side prevents the browser from being used to reverse-engineer
    or tamper with the risk weights.
    """
    grouped = questions_by_category()
    return [
        {
            "category": category,
            "question_count": len(grouped[category]),
            "questions": [
                {
                    "id": q["id"],
                    "text": q["text"],
                    "options": q["options"],
                }
                for q in grouped[category]
            ],
        }
        for category in CATEGORY_ORDER
    ]


# ---------------------------------------------------------------------------
# Printable privacy checklist
# ---------------------------------------------------------------------------
PRIVACY_CHECKLIST = [
    "Review profile visibility",
    "Hide unnecessary contact information (phone, email)",
    "Review birth-date visibility",
    "Review location sharing settings",
    "Avoid unnecessary real-time location posts",
    "Review tagging permissions and enable tag review",
    "Review followers / friends list",
    "Verify unfamiliar connection requests before accepting",
    "Enable multi-factor authentication (MFA)",
    "Enable login alerts where available",
    "Review active sessions and logged-in devices",
    "Review connected third-party applications",
    "Remove unused integrations and revoke old app access",
    "Review old public posts",
    "Review photo privacy and strip EXIF metadata",
    "Be cautious with unexpected links and attachments",
    "Never share verification codes (OTP) with anyone",
    "Review privacy settings periodically (every 3-6 months)",
]