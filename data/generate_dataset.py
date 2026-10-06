"""
generate_dataset.py
===================
Generates 1,000 FULLY SYNTHETIC privacy-assessment records and writes them to
data/social_media_privacy_assessments.csv.

Guarantees
----------
* No real person, account, platform or profile is referenced.
* No scraping, no network calls, no external data.
* Answers are produced from the questionnaire's own option sets.
* Risk scores are computed by the SAME scoring engine used by the app, so the
  dataset is internally consistent with the model.

Usage
-----
    python data/generate_dataset.py
    python data/generate_dataset.py --rows 5000 --seed 7
"""

import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from backend.config import DATASET_PATH  # noqa: E402
from backend.services.questionnaire import QUESTIONS, QUESTION_IDS  # noqa: E402
from backend.services.scoring_engine import (  # noqa: E402
    safest_option,
    riskiest_option,
)

# Archetypes: (name, probability of choosing the risky option)
ARCHETYPES = [
    ("privacy_conscious", 0.05),
    ("average", 0.32),
    ("over_sharer", 0.72),
]


def _pick_answer(question, risky_probability, rng):
    """
    Choose an answer for a question.

    With probability `risky_probability` take the riskiest option; otherwise
    take the safest option, with a small chance of a middle-ground option so
    the dataset is not binary.
    """
    options = question["options"]

    if rng.random() < risky_probability:
        return riskiest_option(question)

    if len(options) > 2 and rng.random() < 0.25:
        # Pick a middle option (neither safest nor riskiest).
        ordered = sorted(options, key=lambda o: question["risk_map"][o])
        return ordered[len(ordered) // 2]

    return safest_option(question)


def generate_rows(rows, seed=42):
    """Return a list of dicts, one per synthetic profile."""
    rng = random.Random(seed)
    archetype_names = [name for name, _ in ARCHETYPES]
    archetype_weights = [0.25, 0.45, 0.30]

    from backend.services.scoring_engine import calculate_privacy_risk

    records = []

    for index in range(rows):
        archetype = rng.choices(archetype_names, weights=archetype_weights, k=1)[0]
        risky_probability = dict(ARCHETYPES)[archetype]

        answers = {
            question["id"]: _pick_answer(question, risky_probability, rng)
            for question in QUESTIONS
        }

        scored = calculate_privacy_risk(answers)

        record = {"profile_id": f"SYN-{index + 1:05d}", "archetype": archetype}
        record.update(answers)
        record["risk_score"] = scored["overall_score"]
        record["risk_level"] = scored["risk_level"]
        records.append(record)

    return records


def main():
    parser = argparse.ArgumentParser(
        description="Generate the synthetic privacy-assessment dataset."
    )
    parser.add_argument("--rows", type=int, default=1000,
                        help="Number of synthetic records (default 1000).")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility (default 42).")
    parser.add_argument("--output", type=str, default=DATASET_PATH,
                        help="Output CSV path.")
    args = parser.parse_args()

    print(f"Generating {args.rows} fully synthetic records (seed={args.seed})...")
    records = generate_rows(args.rows, args.seed)

    frame = pd.DataFrame(records)

    # Column order: identifiers, questionnaire answers, derived results.
    ordered_columns = ["profile_id", "archetype"] + QUESTION_IDS + ["risk_score", "risk_level"]
    frame = frame[ordered_columns]

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    frame.to_csv(args.output, index=False)

    print(f"Wrote {len(frame)} rows to {args.output}")
    print("\nRisk level distribution:")
    print(frame["risk_level"].value_counts().to_string())
    print("\nAverage risk score: {:.2f}".format(frame["risk_score"].mean()))
    print(
        "\nREMINDER: this dataset is entirely synthetic and contains no real "
        "personal data."
    )


if __name__ == "__main__":
    main()