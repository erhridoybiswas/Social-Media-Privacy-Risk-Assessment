# Social Media Privacy Risk Assessment Framework

> **Privacy-focused cybersecurity framework for assessing social-media exposure,
> account-security practices, social-engineering risk, digital-footprint risk,
> and personalized privacy improvements using synthetic/self-reported data.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-black)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57)
![Tests](https://img.shields.io/badge/tests-39%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Overview

The **Social Media Privacy Risk Assessment Framework** is a defensive,
educational privacy-assessment platform. A user answers **51 questions** about
their social-media privacy *settings* — not their personal data — and receives:

- an overall **Privacy Risk Score (0–100)**
- a **Risk Level** (LOW / MODERATE / HIGH / CRITICAL)
- **10 category scores**
- severity-ranked **privacy findings**
- personalised, prioritised **recommendations**
- an **improvement simulator** ("what happens if I fix these settings?")
- an **analytics dashboard**
- a printable **privacy checklist** and **assessment report**

> **A higher score means HIGHER exposure / risk.**

---

## Problem Statement

Social-media users routinely expose far more information than they realise.
Privacy settings drift over time, platforms change defaults, and old posts
persist indefinitely. Most people have no structured way to measure their own
exposure, and existing "privacy checker" tools either require handing over
account credentials or rely on automated scraping.

This project demonstrates that **meaningful privacy-risk assessment is possible
without collecting personal data at all** — using self-reported settings and a
transparent, configurable risk model.

---

## Objectives

1. Build a questionnaire that assesses privacy **configuration**, never personal data.
2. Convert answers into numeric, bounded exposure features (0–100).
3. Aggregate those features into ten category scores and one overall score.
4. Translate numeric risk into human-readable findings and prioritised actions.
5. Provide an improvement simulator that shows the modelled effect of remediation.
6. Follow Privacy-by-Design throughout: data minimisation, purpose limitation,
   secure processing, user control.
7. Produce a GitHub-ready, testable, documented engineering artefact.

---

## Cybersecurity Relevance

| Domain | Relevance |
|---|---|
| Privacy engineering | Data minimisation, purpose limitation, privacy by default |
| Risk management | Multi-criteria weighted risk scoring with severity classification |
| Security awareness | Questionnaire → findings → personalised training output |
| Identity protection | Exposure of identifiers → identity-theft and impersonation risk |
| GRC | Category scores, findings register, control status, exportable reporting |
| Application security | Input validation, rate limiting, no-PII schema, CSP headers |
| SOC / defensive ops | Awareness of social-engineering precursor behaviours |

---

## Privacy vs Security

| | Privacy | Security |
|---|---|---|
| Question | *Who can see my information?* | *Who can access my account?* |
| Failure mode | Overexposure | Unauthorised access |
| Representative controls | Visibility scope, tag review, metadata stripping | MFA, unique passwords, login alerts |

**A social-media account may have a strong password but still expose too much
personal information publicly.**

> **Strong Account Security ≠ Strong Privacy.**

---

## Features

- 51-question privacy questionnaire across 10 categories
- Configurable category weights and risk thresholds
- Feature extraction (answers → 0–100 exposure values)
- Ten category risk scores + one overall score
- Risk classification: LOW / MODERATE / HIGH / CRITICAL
- Findings engine with CRITICAL / HIGH / MEDIUM severity
- Recommendation engine with IMMEDIATE / IMPORTANT / GOOD PRACTICE priorities
- Improvement simulator with before/after comparison
- Radar + bar + doughnut charts (Chart.js)
- Aggregate analytics dashboard
- Print-ready HTML assessment report
- Printable / downloadable privacy checklist
- Safe local EXIF metadata viewer + stripper (no upload)
- 39 automated tests, including PII-schema regression tests

---

## Architecture

```
User
 ↓
Privacy Questionnaire (51 questions / 10 categories)
 ↓
Input Validation (allow-list, type checks, size caps)
 ↓
Feature Extraction (answers → 0–100 risk features)
 ↓
Category Risk Analysis (10 weighted category scores)
 ↓
Risk Scoring Engine (configurable weights)
 ↓
Overall Privacy Risk Score (0–100)
 ↓
Risk Classification (LOW / MODERATE / HIGH / CRITICAL)
 ↓
Findings Engine → Recommendation Engine
 ↓
Privacy Dashboard · Improvement Simulator
 ↓
Privacy Assessment Report
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, Flask 3 |
| Persistence | SQLite 3 (standard library `sqlite3`) |
| Data analysis | pandas (dataset generation) |
| Frontend | HTML5, CSS3, vanilla JavaScript |
| Charts | Chart.js 4 (CDN) |
| Reports | Self-contained HTML (print → PDF) |
| Testing | pytest |

**Why this stack for a student project:** zero infrastructure, fully offline,
no build step, and every layer is explainable line-by-line in an interview.

---

## Privacy Questionnaire

**10 categories · 51 questions · answer vocabularies:**
`YES / NO / SOMETIMES / NOT SURE` and `PUBLIC / FRIENDS / PRIVATE`

| # | Category | Questions |
|---|---|---|
| A | Profile Visibility | 5 |
| B | Personal Information | 7 |
| C | Location Privacy | 6 |
| D | Posts & Content | 5 |
| E | Connections | 4 |
| F | Tagging & Mentions | 4 |
| G | Account Security | 7 |
| H | Third-Party Apps | 3 |
| I | Social Engineering | 5 |
| J | Digital Footprint | 5 |

> The questionnaire **never** asks for an actual phone number, address, birth
> date, or password — only whether such information is *visible*.

---

## Risk Categories

Profile Visibility · Personal Information · Location Privacy · Posts & Content ·
Connections · Tagging & Mentions · Account Security · Third-Party Apps ·
Social Engineering · Digital Footprint

---

## Risk Scoring

**Category score** (weighted mean inside a category):

```
category_score = Σ(risk_value_i × weight_i) / Σ(weight_i)
```

**Overall score** (weighted sum across categories):

| Category | Weight |
|---|---|
| Personal Information | 15% |
| Location Privacy | 15% |
| Account Security | 15% |
| Profile Visibility | 10% |
| Posts & Content | 10% |
| Connections | 10% |
| Social Engineering | 10% |
| Tagging & Mentions | 5% |
| Third-Party Apps | 5% |
| Digital Footprint | 5% |

**Risk bands:**

| Range | Level |
|---|---|
| 0–20 | LOW |
| 21–40 | MODERATE |
| 41–70 | HIGH |
| 71–100 | CRITICAL |

> ⚠️ Weights and thresholds are **educational assumptions**, configurable in
> `backend/config.py`, and must be validated before any professional use.

---

## Privacy Findings

Findings are raised whenever a question's risk contribution reaches the
reporting threshold (default 60). Severity: `CRITICAL ≥ 90`, `HIGH ≥ 75`,
`MEDIUM ≥ 60`.

Example output:

```
OVERALL PRIVACY RISK: 68/100
LEVEL: HIGH

TOP RISKS:
 1. Phone number reported as publicly visible
 2. Real-time location sharing enabled
 3. MFA disabled
 4. Unknown connection requests frequently accepted
 5. Tag review disabled
```

---

## Recommendation Engine

Every finding maps to a defensive, actionable recommendation, sorted into
three priority bands:

- **IMMEDIATE** — act today (account takeover / physical safety impact)
- **IMPORTANT** — act this week (materially reduces exposure)
- **GOOD PRACTICE** — hygiene improvement at the next privacy review

---

## Improvement Simulator

The simulator substitutes the **lowest-risk option** for each selected question
and re-runs the entire scoring pipeline.

```
CURRENT:   72/100  CRITICAL
Changes:   ✓ Make phone private
           ✓ Disable real-time location sharing
           ✓ Enable MFA
           ✓ Enable tag review
NEW:       34/100  MODERATE
Risk reduction: 38 points
```

> This is a **framework simulation**, not a guarantee of real-world safety.

---

## Digital Footprint

- **ACTIVE footprint** — information you deliberately published.
- **PASSIVE footprint** — information generated/collected through online
  activity, depending on service context.

This project evaluates **only self-reported privacy practices**. No external
collection, scraping or tracking occurs at any point.

---

## Social Engineering Awareness

Publicly available context (employer, college, travel plans, interests) makes
social-engineering messages more believable. This project teaches users to
recognise that amplification and to reduce it — **it does not provide attack
scripts or pretexts.**

---

## Account Security

Privacy risk and account-security risk overlap but are not identical.
A fully private profile with MFA disabled remains one credential-stuffing
attack away from full compromise. The framework scores both.

---

## Privacy Dashboard

Cards: Overall Risk · Risk Level · High-Risk Categories · Recommendation Count ·
Security Controls Enabled

Charts: Category Risk Scores · Privacy Risk Distribution · Top Privacy
Weaknesses · Account Security Controls · Digital Footprint Risk ·
Improvement Comparison

---

## Privacy Report

A self-contained, print-ready HTML report containing: assessment reference,
date, overall risk, risk level, category scores, top findings, recommendations,
priority actions, checklist and disclaimer.

**Export:** print the report page → *Save as PDF*, or download the HTML file.

---

## Privacy by Design

| Principle | How this project applies it |
|---|---|
| **Data Minimisation** | Only derived scores + finding types are stored; raw answers are never persisted |
| **Purpose Limitation** | Data is used solely to produce the user's own assessment |
| **Least Privilege** | The app requests no platform credentials, tokens or API access |
| **Privacy by Default** | The report path is entirely non-persistent; saving is explicit |
| **Transparency** | Scoring formula, weights and thresholds are documented and configurable |
| **User Control** | `DELETE /api/assessment/{id}` provides erasure; saving is opt-in |
| **Retention Limitation** | No automatic long-term retention; records are user-deletable |
| **Secure Processing** | Strict allow-list validation, CSP headers, rate limiting, escaped output |

---

## Installation

```bash
# 1. Clone
git clone https://github.com/<your-username>/Social-Media-Privacy-Risk-Assessment.git
cd Social-Media-Privacy-Risk-Assessment

# 2. Virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt

# 4. (Optional) environment file
cp .env.example .env

# 5. Generate the synthetic dataset (1,000 fictional records)
python data/generate_dataset.py

# 6. Run the application
python run.py
```

Open <http://127.0.0.1:5000/>

---

## Usage

1. Open the landing page and click **Start Privacy Assessment**.
2. Either answer the 51 questions yourself, or click **Load Safe Demo Profile**
   to load a fictional high-exposure profile.
3. Click **Generate Privacy Risk Score**.
4. Review your overall score, risk level and category radar chart.
5. Review the findings list and personalised recommendations.
6. Tick the weaknesses you would fix and click **Simulate Improvements**.
7. Open the **Dashboard** for aggregate analytics.
8. Open the **Checklist** page and print or download the checklist.
9. Open the **Report** page to generate a printable HTML report.

---

## API Documentation

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health and question count |
| `GET` | `/api/questionnaire` | Full questionnaire structure |
| `GET` | `/api/privacy-checklist` | Printable checklist items |
| `GET` | `/api/demo-profile` | Fictional demo profile |
| `POST` | `/api/assessment` | Run a full assessment |
| `GET` | `/api/assessment/{id}` | Retrieve a stored assessment |
| `GET` | `/api/assessment/{id}/recommendations` | Recommendations for a record |
| `GET` | `/api/assessment/{id}/report` | HTML report from stored record |
| `POST` | `/api/assessment/report` | HTML report **without persisting** |
| `POST` | `/api/assessment/simulate-improvement` | Before/after simulation |
| `POST` | `/api/assessment/simulate-demo` | Demo profile + simulated fixes |
| `DELETE` | `/api/assessment/{id}` | Delete an assessment (erasure) |
| `GET` | `/api/dashboard/stats` | Aggregate analytics |

**Example request**

```bash
curl -X POST http://127.0.0.1:5000/api/assessment \
  -H "Content-Type: application/json" \
  -d '{
        "answers": {
          "profile_visibility": "PUBLIC",
          "phone_public": "YES",
          "mfa_enabled": "NO",
          "tag_review_enabled": "NO"
        },
        "save": true
      }'
```

**Error contract**

| Status | Code | Meaning |
|---|---|---|
| 400 | `validation_error` | Malformed payload, unknown question ID, invalid option |
| 404 | `not_found` | Assessment does not exist |
| 429 | `rate_limited` | Per-IP request limit exceeded |
| 500 | `server_error` | Generic error (no stack trace leaked) |

---

## Testing

```bash
pytest -v
```

39 automated tests covering:

- extreme profiles (fully private → LOW, fully public → CRITICAL)
- 17 individual risk factors raising the correct category
- score bounds and weight integrity
- all risk-band boundaries (20 / 21 / 40 / 41 / 70 / 71)
- findings and recommendation generation and prioritisation
- improvement simulation (reduces, never increases, zero on safe profile)
- database save / fetch / delete / aggregates
- **schema regression test: no PII-bearing column exists**
- input validation (unknown IDs, invalid options, normalisation, bad payloads)
- report generation content and disclaimer presence
- questionnaire structural integrity and ID uniqueness
- end-to-end orchestration and the fictional demo profile

---

## Security & Privacy Testing

| Test | What it verifies |
|---|---|
| **No PII columns** | `PRAGMA table_info` across all tables contains no `phone`, `email`, `address`, `birth`, `password`, `latitude`, `longitude`, `message`, `answer` column |
| **Input validation** | Only allow-listed question IDs and declared option values are accepted |
| **XSS protection** | All rendered values pass through HTML escaping server-side, plus `esc()` client-side; CSP restricts script sources |
| **API rate limiting** | Per-IP sliding window returns `429` with `Retry-After` |
| **Secure headers** | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, CSP |
| **Environment variables** | Secrets live in `.env` (git-ignored); `.env.example` documents them |
| **Safe report generation** | Reports contain only derived scores and finding types |
| **Data deletion** | `DELETE /api/assessment/{id}` cascades to category scores and findings |
| **No stack-trace leakage** | Global error handler returns generic JSON errors |
| **Local-only metadata tool** | EXIF reader never uploads; stripper writes a copy, never overwrites |

---

## Results

Run against the fictional demo profile (`backend/services/demo_profile.py`):

| Metric | Before | After fixes |
|---|---|---|
| Overall score | high / CRITICAL band | substantially lower / MODERATE band |
| Category scores | 10 categories, weighted | re-computed across all 10 |
| Findings | multiple CRITICAL + HIGH | materially reduced |
| Recommendations | prioritised IMMEDIATE / IMPORTANT / GOOD PRACTICE | reduced count |

Run the app and load the demo profile to reproduce these figures on your own
machine — the exact numbers depend on the weights in `backend/config.py`.

---

## Limitations

- Scores reflect **self-reported** settings and behaviour; inaccurate answers
  produce inaccurate scores.
- Weights and thresholds are **illustrative** and not empirically calibrated
  against breach data.
- The model does **not** represent platform-specific differences in defaults.
- It cannot measure exposure caused by **other people** posting about you.
- It does not assess OSINT discoverability beyond self-reported settings.
- A low score is **not** a guarantee of safety.

---

## Future Improvements

- Platform-specific privacy checklists (per-network settings guides)
- Configurable organisational policy profiles for enterprise awareness programmes
- Privacy-awareness quiz mode with scored learning outcomes
- Privacy maturity scoring with historical trend comparison
- Family / teen safety education module
- GRC reporting export (CSV / JSON findings register)
- Anonymous organisational trend analysis (k-anonymity thresholding)
- Better risk-model calibration against published breach and exposure research
- Localisation and accessibility (screen-reader support, WCAG AA)
- Time-series report comparison ("your privacy posture over 12 months")
- Secure client-side-only assessment mode (WebAssembly / local storage)
- Optional fully offline mode with no database at all

> No invasive monitoring, scraping or tracking will ever be added.

---

## Screenshots

| File | Description |
|---|---|
| `screenshots/01-project-folder-structure.png` | Repository layout |
| `screenshots/02-architecture-diagram.png` | System architecture |
| `screenshots/03-homepage.png` | Landing page |
| `screenshots/04-questionnaire-top.png` | Questionnaire start |
| `screenshots/05-profile-privacy-section.png` | Category A questions |
| `screenshots/06-personal-information-section.png` | Category B questions |
| `screenshots/07-location-section.png` | Category C questions |
| `screenshots/08-account-security-section.png` | Category G questions |
| `screenshots/09-social-engineering-section.png` | Category I questions |
| `screenshots/10-overall-risk-score.png` | Score + risk level cards |
| `screenshots/11-category-scores-table.png` | Category breakdown |
| `screenshots/12-privacy-risk-radar.png` | Radar chart |
| `screenshots/13-top-findings.png` | Findings list |
| `screenshots/14-recommendations.png` | Recommendation list |
| `screenshots/15-improvement-simulator-before.png` | Simulator input |
| `screenshots/16-improvement-simulator-after.png` | Simulator result |
| `screenshots/17-risk-reduction.png` | Before/after comparison |
| `screenshots/18-privacy-dashboard.png` | Dashboard cards |
| `screenshots/19-risk-distribution-chart.png` | Distribution doughnut |
| `screenshots/20-top-weakness-chart.png` | Weakness bar chart |
| `screenshots/21-privacy-checklist.png` | Checklist page |
| `screenshots/22-privacy-report.png` | Generated report |
| `screenshots/23-synthetic-dataset.png` | CSV preview |
| `screenshots/24-automated-tests.png` | `pytest -v` output |
| `screenshots/25-security-privacy-tests.png` | PII-schema test passing |
| `screenshots/26-database-schema.png` | SQLite schema |
| `screenshots/27-github-commits.png` | Commit history |
| `screenshots/28-github-repository.png` | Repository page |
| `screenshots/29-readme-preview.png` | README rendering |

---

## Learning Outcomes

- Designed and implemented a **transparent, configurable multi-criteria risk model**
- Built a **privacy-by-design** system that collects **zero personal data**
- Applied **strict input validation** and defence-in-depth web hardening
- Wrote **39 automated tests**, including a **schema-level PII regression test**
- Generated and analysed a **1,000-record synthetic dataset**
- Produced **industry-style deliverables**: findings, recommendations, report, dashboard
- Practised **GRC concepts**: risk scoring, severity classification, control mapping
- Documented the project to a **portfolio and interview-ready** standard

---

## Ethical Disclaimer

> This project is designed for **defensive cybersecurity and privacy education**.
> It uses **synthetic or voluntarily provided assessment responses** and does
> **not** scrape, track, or profile real social-media users.
>
> The framework **never** requests actual phone numbers, addresses, birth dates,
> passwords, or any other personal data. It assesses **privacy configuration**,
> not people.
>
> Risk weights and thresholds are **educational assumptions**. A high or low
> score is **not** a guarantee that an account will or will not be compromised.

---

## Author

**HRIDOY BISWAS**

- GitHub: [@your-username](https://github.com/erhridoybiswas)
- LinkedIn: [linkedin.com/in/your-profile](https://linkedin.com/in/erhridoybiswas)
