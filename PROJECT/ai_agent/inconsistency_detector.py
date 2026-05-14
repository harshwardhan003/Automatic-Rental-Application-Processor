"""
AI Agent Module 3: Inconsistency Detector
Cross-references documents to find contradictions or gaps.
"""

from pathlib import Path
import csv
from config.settings import OLLAMA_MODEL
from ai_agent.prompts import INCONSISTENCY_DETECTOR_SYSTEM, INCONSISTENCY_DETECTOR_USER_TEMPLATE
from ai_agent.reference_scorer import call_ollama_json

def detect_inconsistencies(app: dict) -> dict:
    """Detect inconsistencies across all submitted documents."""
    folder = Path(app["folder_path"])
    
    # Load all document contents
    def read_file(name):
        p = folder / name
        return p.read_text(encoding="utf-8", errors="replace") if p.exists() else "File missing."

    user_prompt = INCONSISTENCY_DETECTOR_USER_TEMPLATE.format(
        applicant_name=app["applicant_name"],
        ref_number=app["ref_number"],
        form_data_summary=read_file("application_form.csv"),
        payslip_data_summary=read_file("proof_of_income.csv"),
        employer_reference_text=read_file("employer_reference.txt"),
        landlord_reference_text=read_file("landlord_reference.txt"),
        cover_letter_text=read_file("cover_letter.txt")
    )
    
    if OLLAMA_MODEL == "mock":
        risk = "Low"
        findings = []
        if app["ref_number"] == "REF-2026-004": # Emma Walsh discrepancy
            risk = "Medium"
            findings = [{"description": "Income gap of 700 between form and payslip"}]
        elif app["ref_number"] == "REF-2026-013": # Timeline inconsistency
            risk = "Medium"
            findings = [{"description": "Tenancy dates mismatch"}]
            
        return {
            "overall_risk_level": risk,
            "total_inconsistencies_found": len(findings),
            "findings": findings,
            "overall_summary": f"Mock inconsistency analysis. Risk: {risk}"
        }

    try:
        return call_ollama_json(INCONSISTENCY_DETECTOR_SYSTEM, user_prompt)
    except Exception as e:
        print(f"  [AI ERROR] {app['ref_number']} inconsistency: {e}")
        return {"overall_risk_level": "Low", "findings": [], "overall_summary": "Error during analysis."}

def run_inconsistency_detection(applications: list[dict]) -> list[dict]:
    """Runs inconsistency detection for all applicants."""
    print("STAGE 4.3: INCONSISTENCY DETECTION (AI)")
    
    for app in applications:
        print(f"  [AI] Checking consistency for {app['ref_number']}...")
        result = detect_inconsistencies(app)
        app["inconsistency_risk"] = result.get("overall_risk_level", "Low")
        app["inconsistency_findings"] = result.get("findings", [])
        app["inconsistency_summary"] = result.get("overall_summary", "")
        
    return applications
