"""
RPA Module 3: Income Ratio Checker
Reads monthly income from application form and proof of income.
Cross-checks against property rent threshold.
Auto-rejects below hard threshold; flags between soft and hard.
"""

import csv
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import (
    INCOME_MULTIPLIER_REQUIRED,
    INCOME_SOFT_REJECT_THRESHOLD
)
from rpa.tracker_updater import update_income_data
from rpa.email_sender import send_income_rejection_email
from rpa.property_manager import get_property


def load_monthly_rent_for_app(app: dict) -> float:
    """Load the monthly rent for the property the applicant applied for."""
    prop_id = app.get("property_id", "PROP-001")
    prop = get_property(prop_id)
    if not prop:
        print(f"  [WARN] Property {prop_id} not found. Defaulting to €2,000 rent.")
        return 2000.0
    return float(prop.get("rent", 2000))


def read_income_from_form(folder: Path) -> tuple[float, str]:
    """
    Reads declared income from application_form.csv.
    Returns (income_value, source_label).
    """
    form_path = folder / "application_form.csv"
    with open(form_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = {row["field"]: row["value"] for row in reader}
    declared_income = float(data.get("monthly_gross_income", 0))
    return declared_income, "application_form"


def read_income_from_payslip(folder: Path) -> tuple[float | None, str]:
    """
    Reads income from proof_of_income.csv.
    Returns (income_value, source_label) or (None, ...) if not available.
    """
    payslip_path = folder / "proof_of_income.csv"
    if not payslip_path.exists():
        return None, "payslip_missing"
    
    with open(payslip_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = {row["field"]: row["value"] for row in reader}
    
    payslip_income = float(data.get("gross_monthly_income", 0))
    return payslip_income, "proof_of_income"


def check_income(app: dict, monthly_rent: float) -> dict:
    """
    Runs the full income check for one application.
    Sets income_ratio, income_score, and income_status.
    """
    folder = Path(app["folder_path"])
    
    # Only run income check if documents passed
    if not app.get("doc_check_passed", False):
        app["income_check_skipped"] = True
        return app
    
    declared_income, _ = read_income_from_form(folder)
    payslip_income, payslip_source = read_income_from_payslip(folder)
    
    # Use payslip as authoritative if available; else use declared
    authoritative_income = payslip_income if payslip_income is not None else declared_income
    income_ratio = authoritative_income / monthly_rent
    
    # Check for discrepancy between declared and payslip
    income_discrepancy = None
    if payslip_income is not None and declared_income > 0:
        discrepancy = abs(declared_income - payslip_income)
        discrepancy_pct = (discrepancy / declared_income) * 100
        if discrepancy > 200:  # > €200/month difference = flag
            income_discrepancy = {
                "declared": declared_income,
                "payslip": payslip_income,
                "difference": discrepancy,
                "difference_pct": round(discrepancy_pct, 1)
            }
    
    # Income score (0–100): mapped from ratio
    # Ratio 3.0 = score 60 (minimum pass)
    # Ratio 4.0+ = score 100
    if income_ratio >= 4.0:
        income_score = 100
    elif income_ratio >= 3.0:
        income_score = 60 + int((income_ratio - 3.0) / 1.0 * 40)
    else:
        income_score = int(income_ratio / 3.0 * 60)
    
    # Determine outcome
    if income_ratio < INCOME_SOFT_REJECT_THRESHOLD:
        income_status = "Rejected - Income Below Threshold"
        app["status"] = income_status
        print(f"  [INCOME] {app['ref_number']} [FAIL] Ratio {income_ratio:.2f}x - AUTO REJECT")
        send_income_rejection_email(app, income_ratio, monthly_rent)
    elif income_ratio < INCOME_MULTIPLIER_REQUIRED:
        income_status = "Income - Borderline (Flagged)"
        app["status"] = "Eligible - Income Flagged"
        print(f"  [INCOME] {app['ref_number']} [WARN] Ratio {income_ratio:.2f}x - BORDERLINE, proceeding with flag")
    else:
        income_status = "Income Eligible"
        app["status"] = "Eligible - Proceeding to AI Scoring"
        print(f"  [INCOME] {app['ref_number']} [OK] Ratio {income_ratio:.2f}x - ELIGIBLE")
    
    app["income_ratio"] = round(income_ratio, 2)
    app["income_score"] = income_score
    app["income_status"] = income_status
    app["declared_income"] = declared_income
    app["authoritative_income"] = authoritative_income
    app["income_discrepancy"] = income_discrepancy
    app["income_eligible"] = income_ratio >= INCOME_SOFT_REJECT_THRESHOLD
    
    update_income_data(app)
    return app


def run_income_checks(applications: list[dict]) -> list[dict]:
    """Run income checks across all complete applications."""
    print("\n" + "="*60)
    print("STAGE 3: INCOME THRESHOLD CHECK (RPA)")
    print("="*60)
    
    checked = []
    for app in applications:
        monthly_rent = load_monthly_rent_for_app(app)
        print(f"  [INCOME] Processing {app['ref_number']} (Target Rent: €{monthly_rent:,.0f})")
        checked.append(check_income(app, monthly_rent))
    
    eligible = sum(1 for a in checked if a.get("income_eligible", False))
    rejected = sum(1 for a in checked if "Rejected" in a.get("income_status", ""))
    skipped = sum(1 for a in checked if a.get("income_check_skipped", False))
    
    print(f"\n[INCOME CHECK] Complete.")
    print(f"  Eligible: {eligible} | Auto-rejected: {rejected} | Skipped (incomplete docs): {skipped}\n")
    return checked
