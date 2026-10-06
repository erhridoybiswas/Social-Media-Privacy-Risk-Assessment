"""
database.py
===========
SQLite persistence layer.

PRIVACY-BY-DESIGN RULES ENFORCED HERE
-------------------------------------
The schema stores ONLY:
    * assessment_id
    * overall_score
    * risk_level
    * created_at
    * category scores
    * finding TYPES (question IDs) + severity + a generic description

The schema NEVER stores:
    * phone numbers
    * email addresses
    * home addresses
    * birth dates
    * passwords
    * exact locations
    * private messages
    * raw questionnaire answers

A regression test (tests/test_privacy_engine.py) asserts that no such column
exists in any table.
"""

import os
import sqlite3
from contextlib import contextmanager

from backend.config import DB_PATH

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS assessments (
    assessment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    overall_score   REAL    NOT NULL,
    risk_level      TEXT    NOT NULL,
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS category_scores (
    category_score_id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id     INTEGER NOT NULL,
    category          TEXT    NOT NULL,
    score             REAL    NOT NULL,
    FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS findings (
    finding_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    category      TEXT    NOT NULL,
    finding_type  TEXT    NOT NULL,
    severity      TEXT    NOT NULL,
    description   TEXT    NOT NULL,
    FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    finding_type      TEXT NOT NULL UNIQUE,
    recommendation    TEXT NOT NULL,
    priority          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_category_scores_assessment
    ON category_scores(assessment_id);
CREATE INDEX IF NOT EXISTS idx_findings_assessment
    ON findings(assessment_id);
"""

# Columns that must NEVER exist in this database. Used by tests.
FORBIDDEN_COLUMN_TOKENS = (
    "phone", "email", "address", "birth", "dob", "password",
    "latitude", "longitude", "gps", "location_exact", "message",
    "answer", "ssn", "credit",
)


@contextmanager
def get_connection(db_path=None):
    """Context manager yielding a row-factory-enabled SQLite connection."""
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db(db_path=None):
    """Create the schema if it does not already exist."""
    with get_connection(db_path) as connection:
        connection.executescript(SCHEMA)


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------
def save_assessment(result, db_path=None):
    """
    Persist a derived assessment result.

    Only non-sensitive, derived values are written.
    Returns the new assessment_id.
    """
    with get_connection(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO assessments (overall_score, risk_level, created_at) "
            "VALUES (?, ?, ?)",
            (
                float(result["overall_score"]),
                result["risk_level"],
                result["created_at"],
            ),
        )
        assessment_id = cursor.lastrowid

        for category, score in result["category_scores"].items():
            cursor.execute(
                "INSERT INTO category_scores (assessment_id, category, score) "
                "VALUES (?, ?, ?)",
                (assessment_id, category, float(score)),
            )

        for finding in result["findings"]:
            cursor.execute(
                "INSERT INTO findings "
                "(assessment_id, category, finding_type, severity, description) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    assessment_id,
                    finding["category"],
                    finding["finding_type"],
                    finding["severity"],
                    finding["description"],
                ),
            )

        return assessment_id


def seed_recommendations(db_path=None):
    """Populate the static recommendation catalogue from the questionnaire."""
    from backend.services.questionnaire import QUESTIONS

    with get_connection(db_path) as connection:
        cursor = connection.cursor()
        for question in QUESTIONS:
            cursor.execute(
                "INSERT OR REPLACE INTO recommendations "
                "(finding_type, recommendation, priority) VALUES (?, ?, ?)",
                (question["id"], question["recommendation"], question["priority"]),
            )


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------
def get_assessment(assessment_id, db_path=None):
    """Fetch one assessment with its category scores and findings."""
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM assessments WHERE assessment_id = ?",
            (assessment_id,),
        ).fetchone()
        if row is None:
            return None

        categories = connection.execute(
            "SELECT category, score FROM category_scores WHERE assessment_id = ?",
            (assessment_id,),
        ).fetchall()

        findings = connection.execute(
            "SELECT category, finding_type, severity, description "
            "FROM findings WHERE assessment_id = ?",
            (assessment_id,),
        ).fetchall()

    return {
        "assessment_id": row["assessment_id"],
        "overall_score": row["overall_score"],
        "risk_level": row["risk_level"],
        "created_at": row["created_at"],
        "category_scores": {c["category"]: c["score"] for c in categories},
        "findings": [dict(f) for f in findings],
    }


def get_recommendations(db_path=None):
    """Return the static recommendation catalogue."""
    with get_connection(db_path) as connection:
        rows = connection.execute(
            "SELECT finding_type, recommendation, priority FROM recommendations"
        ).fetchall()
    return [dict(row) for row in rows]


def get_recommendations_for(assessment_id, db_path=None):
    """Recommendations relevant to a stored assessment's findings."""
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT r.finding_type, r.recommendation, r.priority
            FROM findings f
            JOIN recommendations r ON r.finding_type = f.finding_type
            WHERE f.assessment_id = ?
            ORDER BY
                CASE r.priority
                    WHEN 'IMMEDIATE' THEN 0
                    WHEN 'IMPORTANT' THEN 1
                    ELSE 2
                END
            """,
            (assessment_id,),
        ).fetchall()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Aggregates (dashboard)
# ---------------------------------------------------------------------------
def get_dashboard_stats(db_path=None):
    """Aggregate statistics over stored assessments (no PII involved)."""
    with get_connection(db_path) as connection:
        total = connection.execute(
            "SELECT COUNT(*) AS c FROM assessments"
        ).fetchone()["c"]

        average = connection.execute(
            "SELECT AVG(overall_score) AS a FROM assessments"
        ).fetchone()["a"] or 0.0

        distribution_rows = connection.execute(
            "SELECT risk_level, COUNT(*) AS c FROM assessments GROUP BY risk_level"
        ).fetchall()

        category_rows = connection.execute(
            "SELECT category, AVG(score) AS avg_score, COUNT(*) AS c "
            "FROM category_scores GROUP BY category"
        ).fetchall()

        finding_rows = connection.execute(
            "SELECT finding_type, COUNT(*) AS c FROM findings "
            "GROUP BY finding_type ORDER BY c DESC LIMIT 10"
        ).fetchall()

    return {
        "total_assessments": total,
        "average_score": round(average, 2),
        "risk_distribution": {r["risk_level"]: r["c"] for r in distribution_rows},
        "category_averages": {
            r["category"]: round(r["avg_score"], 2) for r in category_rows
        },
        "top_weaknesses": [
            {"finding_type": r["finding_type"], "count": r["c"]}
            for r in finding_rows
        ],
    }


# ---------------------------------------------------------------------------
# Deletion (user control / right to erasure)
# ---------------------------------------------------------------------------
def delete_assessment(assessment_id, db_path=None):
    """Delete an assessment and all dependent rows. Returns True if deleted."""
    with get_connection(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM assessments WHERE assessment_id = ?",
            (assessment_id,),
        )
        return cursor.rowcount > 0


def delete_all(db_path=None):
    """Wipe every assessment. Used by tests and by the 'reset' admin action."""
    with get_connection(db_path) as connection:
        connection.executescript(
            "DELETE FROM findings;"
            "DELETE FROM category_scores;"
            "DELETE FROM assessments;"
        )