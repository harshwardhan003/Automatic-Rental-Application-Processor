"""
AI Agent Module 2: Cover Letter Analyser
Analyses cover letters for motivation, stability, and suitability.
"""

from pathlib import Path
import csv
from config.settings import OLLAMA_MODEL
from ai_agent.prompts import COVER_LETTER_SYSTEM, COVER_LETTER_USER_TEMPLATE
from ai_agent.reference_scorer import call_ollama_json
from rpa.property_manager import get_property

def analyse_cover_letter(app: dict) -> dict:
    """Analyse the cover letter of one applicant."""
    folder = Path(app["folder_path"])
    letter_path = folder / "cover_letter.txt"
    
    if not letter_path.exists():
        return {"score": 0, "summary": "Missing cover letter."}
    
    with open(letter_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    
    # Property context
    prop = get_property(app.get("property_id", "PROP-001"))
    prop_str = f"Address: {prop['address']}, Rent: €{prop['rent']}, Requirements: {prop['requirements']}"
    
    # Need form data for context
    form_path = folder / "application_form.csv"
    with open(form_path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        form_data = {row["field"]: row["value"] for row in reader}

    system_prompt = COVER_LETTER_SYSTEM.format(property_details=prop_str)
    user_prompt = COVER_LETTER_USER_TEMPLATE.format(
        applicant_name=app["applicant_name"],
        ref_number=app["ref_number"],
        property_address=prop["address"],
        property_rent=prop["rent"],
        declared_income=app.get("declared_income", 0),
        employment_type=form_data.get("employment_type", "Unknown"),
        employer_name=form_data.get("employer_name", "Unknown"),
        reason_for_moving=form_data.get("reason_for_moving", "Unknown"),
        num_occupants=form_data.get("num_occupants", 1),
        cover_letter_text=text
    )
    
    if OLLAMA_MODEL == "mock":
        return {
            "score": 7,
            "motivation_score": 8,
            "stability_indicators": ["Long-term interest"],
            "concerning_signals": [],
            "summary": "Mock cover letter analysis."
        }

    try:
        return call_ollama_json(system_prompt, user_prompt)
    except Exception as e:
        print(f"  [AI ERROR] {app['ref_number']} cover letter: {e}")
        return {"score": 5, "summary": f"Analysis error: {str(e)}"}

def run_cover_letter_analysis(applications: list[dict]) -> list[dict]:
    """Runs cover letter analysis for all applicants."""
    print("STAGE 4.2: COVER LETTER ANALYSIS (AI)")

    
    for app in applications:
        print(f"  [AI] Analysing cover letter for {app['ref_number']}...")
        result = analyse_cover_letter(app)
        app["cover_letter_score"] = result.get("score", 0)
        app["cover_letter_summary"] = result.get("summary", "")
        app["cover_letter_concerns"] = result.get("concerning_signals", [])
        
    return applications
