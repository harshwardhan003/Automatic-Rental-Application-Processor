# DRAP — Dublin Rental Application Processor

> A hybrid RPA and AI agent system for automated rental application screening, built for Clarendon Residential.

---

## Overview

DRAP is a production-style intelligent automation system that processes rental applications end-to-end for a fictional Dublin letting agency. It combines **rule-based Robotic Process Automation (RPA)** for structured validation tasks with a **locally hosted LLaMA 3 AI agent** for qualitative scoring of references, cover letters, and inconsistency detection. Results are surfaced through a **Streamlit dashboard** for letting agents to review, shortlist, and action applicants.

The system was built as part of the H9IAPA (Intelligent Agents and Process Automation) module at National College of Ireland.

---

## Features

- **Automated document intake** — reads structured application folders, validates required documents, and flags missing submissions
- **Income eligibility screening** — enforces a 3x rent multiplier rule with a soft-reject threshold at 2.75x
- **AI-powered reference scoring** — LLM evaluates employer and landlord references for specificity, enthusiasm, red flags, and authenticity
- **Cover letter analysis** — LLM scores motivational quality, property fit, and stability indicators; bias-aware (does not penalise non-native English writers)
- **Inconsistency detection** — cross-checks application form fields against references and cover letter for contradictions
- **Composite scoring engine** — weighted scoring across five dimensions to generate a final score out of 100
- **Ranked shortlist generation** — top candidates ranked and exported to CSV
- **Automated email drafting** — generates viewing invitations, AI rejections, income rejections, and missing document requests
- **GDPR compliance ledger** — SQLite database tracking consent, purpose, and scheduled 90-day deletion
- **Bias audit** — statistical analysis of score variance by name origin and cover letter word count
- **Property matching intelligence** — dynamically re-scores all applicants against any property in the portfolio
- **Streamlit dashboard** — six-page UI for portfolio overview, applicant analysis, email drafting, and property management

---

## Project Structure

```
PROJECT/
├── app.py                          # Streamlit dashboard (6 pages)
├── main.py                         # CLI entry point and pipeline orchestrator
├── generate_data.py                # Synthetic applicant data generator
│
├── ai_agent/
│   ├── prompts.py                  # All LLM system prompts and user templates
│   ├── reference_scorer.py         # Scores employer + landlord references via LLM
│   ├── cover_letter_analyser.py    # Analyses motivation and stability signals
│   ├── inconsistency_detector.py   # Cross-checks application data for contradictions
│   ├── composite_scorer.py         # Weighted score aggregation and report generation
│   ├── bias_auditor.py             # Statistical bias audit on scoring outputs
│   └── matcher.py                  # Property-to-applicant matching engine
│
├── rpa/
│   ├── intake_processor.py         # Reads application folders, builds application objects
│   ├── document_validator.py       # Checks for required documents, flags missing ones
│   ├── income_checker.py           # Validates income eligibility against rent thresholds
│   ├── email_sender.py             # Sends or simulates outcome emails
│   ├── email_templates.py          # Email copy for each outcome type
│   ├── tracker_updater.py          # Writes results to Excel tracker
│   ├── property_manager.py         # CRUD operations on the property portfolio
│   └── gdpr_ledger.py              # SQLite-backed GDPR consent and deletion tracking
│
├── config/
│   └── settings.py                 # All thresholds, weights, paths, and API settings
│
├── data/
│   ├── properties.csv              # Property portfolio
│   └── applications/
│       └── REF-2026-XXX/           # One folder per applicant (structured intake format)
│           ├── application_form.csv
│           ├── cover_letter.txt
│           ├── employer_reference.txt
│           ├── landlord_reference.txt
│           ├── proof_of_income.csv
│           └── photo_id_present.txt
│
├── output/
│   ├── applications_master.xlsx    # Full pipeline tracker (all applicants)
│   ├── shortlist_ranked.csv        # Top candidates ranked by composite score
│   ├── email_log.csv               # Log of all emails sent or simulated
│   ├── bias_audit_report.txt       # Bias audit findings and recommendations
│   └── individual_reports/         # Per-applicant JSON + TXT score reports
│
└── bpmn/
    ├── as_is_bpmn.png              # Current process (manual) BPMN diagram
    └── to_be_bpmn.png              # Automated process (DRAP) BPMN diagram
```

---

## AI Scoring Weights

| Dimension | Weight | Description |
|---|---|---|
| Income Score | 25% | Financial eligibility relative to rent |
| Employer Reference | 20% | Employment stability, specificity, enthusiasm |
| Landlord Reference | 15% | Tenancy track record and conduct |
| Cover Letter | 15% | Motivation, property fit, stability signals |
| Inconsistency Penalty | 15% | Applied as a negative modifier for contradictions |
| Document Completeness | 10% | Submission professionalism and organisation |

---

## Pipeline Stages

```
Stage 1 — Intake
  └── Reads all application folders, builds structured application objects

Stage 2 — Document Validation (RPA)
  └── Checks all 6 required documents are present; flags missing submissions

Stage 3 — Income Check (RPA)
  └── Validates monthly income >= 3x rent; soft-rejects below 2.75x

Stage 4 — AI Scoring (LLaMA 3 via Ollama)
  ├── Reference scoring (employer + landlord)
  ├── Cover letter analysis
  └── Inconsistency detection

Stage 5 — Composite Scoring
  ├── Weighted aggregation of all scores
  ├── Individual report generation (JSON + TXT)
  └── Ranked shortlist export (CSV)

Stage 5.1 — Automated Emails
  └── Viewing invitations for shortlisted; rejection emails for others

Stage 6 — Bias Audit
  └── Statistical analysis of score distributions and potential biases
```

---

## Setup and Installation

### Prerequisites

- Python 3.13+
- [Ollama](https://ollama.com/) installed and running locally
- LLaMA 3 model pulled via Ollama

```bash
# Pull the LLaMA 3 model
ollama pull llama3
```

### Install Dependencies

```bash
# Clone the repo and navigate to the project folder
cd PROJECT

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration

Copy `.env` and configure:

```
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3
EMAIL_SIMULATION_MODE=True
AGENCY_EMAIL=applications@clarendonresidential.ie
```

---

## Usage

### CLI

```bash
# Run the complete pipeline
python main.py run

# Target a specific property
python main.py run --prop PROP-001

# Run RPA stages only
python main.py rpa

# Run AI scoring only (requires RPA to have run first)
python main.py score

# Run bias audit on existing results
python main.py audit

# Check environment and Ollama connection
python main.py check

# View GDPR consent ledger
python main.py gdpr

# Reset all outputs and start fresh
python main.py reset
```

### Streamlit Dashboard

```bash
streamlit run app.py
```

The dashboard opens at `http://localhost:8501` with six pages:

| Page | Description |
|---|---|
| System Dashboard | Portfolio overview, pipeline controls, KPI metrics |
| Property Intelligence | Dynamic applicant matching across all properties |
| Application Hub | Upload new application ZIPs for intake |
| Email Draft Terminal | Generate and send outcome emails per applicant |
| Applicant Analysis | Deep score breakdown with AI narrative |
| Property Manager | Add and manage properties in the portfolio |

---

## Application Folder Format

Each applicant must submit a folder named `REF-YYYY-XXX/` containing:

| File | Format | Required |
|---|---|---|
| `application_form.csv` | CSV (name, DOB, income, preferences) | Yes |
| `cover_letter.txt` | Plain text | Yes |
| `employer_reference.txt` | Plain text | Yes |
| `landlord_reference.txt` | Plain text | Yes |
| `proof_of_income.csv` | CSV (month, net_income) | Yes |
| `photo_id_present.txt` | `yes` or `no` | Yes |

To generate synthetic test data:

```bash
python generate_data.py
```

---

## Output Files

| File | Description |
|---|---|
| `output/applications_master.xlsx` | Full tracker with all applicant statuses |
| `output/shortlist_ranked.csv` | Top candidates ranked by composite score |
| `output/individual_reports/` | Per-applicant score breakdowns and AI narratives |
| `output/email_log.csv` | Log of all simulated/sent emails |
| `output/bias_audit_report.txt` | Statistical bias findings and recommendations |
| `output/gdpr_ledger.db` | SQLite GDPR consent and deletion schedule |

---

## Sample Report Output

```
DRAP APPLICANT REPORT
============================================================
Reference:       REF-2026-001
Applicant:       Niamh Fitzgerald
Status:          Eligible — Proceeding to AI Scoring

COMPOSITE SCORE: 86.5 / 100
RECOMMENDATION:  Good Candidate

SCORE BREAKDOWN:
  Income Score:              100
  Employer Reference Score:   70
  Landlord Reference Score:   70
  Cover Letter Score:         80
  Document Completeness:     100
  Inconsistency Base Score:  100

AI SUMMARY:
Niamh Fitzgerald presents a strong profile with exceptional financial
stability and clear personal motivation. Minor omissions in reference
detail warrant follow-up but do not materially weaken the application.

RED FLAGS:
  [!] Some notable omissions in the description of qualifications
  [!] Absence of information about noise or property conduct history
```

---

## GDPR Compliance

The system maintains a SQLite ledger (`gdpr_ledger.db`) tracking:

- Applicant name and reference number
- Consent timestamp and stated processing purpose
- Scheduled deletion date (90 days after decision by default)

To view the current ledger:

```bash
python main.py gdpr
```

The retention period and agency details are configurable in `config/settings.py`.

---

## Bias Audit

The bias auditor runs automatically at the end of each pipeline and checks for:

- **Name origin correlation** — compares average composite scores between Irish-origin and other-origin names (flagged if statistically significant at p < 0.05)
- **Cover letter word count correlation** — checks whether longer letters correlate with higher scores (flags writers who may be advantaged by prose volume)

A sample audit finding:

> *Minor Concern — Monitor. A statistically significant correlation between cover letter word count and composite score was detected (p < 0.05). Name origin comparison did not reach significance (p = 0.2).*

---

## Configuration Reference

All thresholds and weights are centralised in `config/settings.py`:

```python
INCOME_MULTIPLIER_REQUIRED = 3.0        # Income must be >= 3x monthly rent
INCOME_SOFT_REJECT_THRESHOLD = 2.75     # Below this: auto-reject
SHORTLIST_SIZE = 10                     # Max candidates on shortlist
GDPR_DATA_RETENTION_DAYS = 90          # Days before deletion scheduled
EMAIL_SIMULATION_MODE = True            # True: log to file, False: send via SMTP
BIAS_AUDIT_SCORE_VARIANCE_THRESHOLD = 10.0
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Dashboard | Streamlit |
| AI Agent | LLaMA 3 (via Ollama, local inference) |
| LLM API | OpenAI-compatible REST (Ollama) |
| RPA Layer | Python (custom rule-based automation) |
| Data Storage | SQLite (GDPR), Excel (tracker), JSON (reports), CSV (shortlist) |
| Visualisation | Streamlit native metrics and tables |

---

## Author

**Harshwardhan Vijay Dongare**
MSc Artificial Intelligence, National College of Ireland, Dublin
[GitHub](https://github.com/harshwardhan003) | [Portfolio](https://harshwardhanweb.netlify.app) | [LinkedIn](https://www.linkedin.com/in/harshwardhan-dongare-a25122199/)

---

## Acknowledgements

Built as part of the H9IAPA (Intelligent Agents and Process Automation) module at National College of Ireland. All applicant data used in this system is entirely synthetic, generated programmatically for demonstration purposes. Clarendon Residential is a fictional agency created for this assignment.
