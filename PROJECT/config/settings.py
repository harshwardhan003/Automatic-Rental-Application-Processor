"""
DRAP System Configuration
All thresholds, file paths, weights, and API settings live here.
Modify this file to adapt the system to different properties or criteria.
"""

import os
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
APPLICATIONS_DIR = DATA_DIR / "applications"
OUTPUT_DIR = BASE_DIR / "output"
REPORTS_DIR = OUTPUT_DIR / "individual_reports"
TRACKER_PATH = OUTPUT_DIR / "applications_master.xlsx"
SHORTLIST_PATH = OUTPUT_DIR / "shortlist_ranked.csv"
EMAIL_LOG_PATH = OUTPUT_DIR / "email_log.csv"
BIAS_AUDIT_PATH = OUTPUT_DIR / "bias_audit_report.txt"
GDPR_DB_PATH = OUTPUT_DIR / "gdpr_ledger.db"
PROPERTIES_PATH = DATA_DIR / "properties.csv"

# ─── RPA Settings ─────────────────────────────────────────────────────────────
REQUIRED_DOCUMENTS = [
    "application_form.csv",
    "cover_letter.txt",
    "employer_reference.txt",
    "landlord_reference.txt",
    "proof_of_income.csv",
    "photo_id_present.txt",
]

INCOME_MULTIPLIER_REQUIRED = 3.0      # Monthly income must be >= 3x monthly rent
INCOME_SOFT_REJECT_THRESHOLD = 2.75   # Below this: auto-reject. Between 2.75-3.0: flag only
RESUBMISSION_WINDOW_HOURS = 48
SHORTLIST_SIZE = 10                   # How many to present to letting agent

# ─── AI Scoring Weights ───────────────────────────────────────────────────────
SCORING_WEIGHTS = {
    "income_score": 0.25,         # 25% — financial eligibility
    "employer_reference": 0.20,   # 20% — employment stability signals
    "landlord_reference": 0.15,   # 15% — tenancy track record
    "cover_letter": 0.15,         # 15% — motivation and stability indicators
    "inconsistency_penalty": 0.15, # 15% — applied as negative modifier
    "document_completeness": 0.10, # 10% — professionalism/organisation
}

# ─── AI API Settings ──────────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "llama3" 
AI_MAX_TOKENS = 3500 # Sufficient for local context

# ─── Email Settings (simulation mode) ────────────────────────────────────────
EMAIL_SIMULATION_MODE = True    # True = write to file, False = real SMTP
AGENCY_EMAIL = "applications@clarendonresidential.ie"
AGENCY_NAME = "Clarendon Residential"
AGENT_NAME = "Siobhán Ní Bhriain"

# ─── GDPR Settings ────────────────────────────────────────────────────────────
GDPR_DATA_RETENTION_DAYS = 90   # Days after decision before deletion scheduled

def get_gdpr_purpose(property_address: str = "14 Charleston Road, Ranelagh") -> str:
    return f"Rental application processing for {property_address}"

# ─── Bias Audit Settings ──────────────────────────────────────────────────────
BIAS_AUDIT_SCORE_VARIANCE_THRESHOLD = 10.0  # Flag if group variance > 10 points
MIN_COVER_LETTER_WORD_COUNT_WARNING = 80    # Flag if < 80 words (may penalise writers)
