"""
AI Agent Module 4: Composite Scorer
Aggregates all AI component scores into a final weighted score.
Generates the ranked shortlist and per-applicant report files.
"""

import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import (
    SCORING_WEIGHTS, SHORTLIST_PATH, REPORTS_DIR, OUTPUT_DIR, OLLAMA_MODEL
)
from ai_agent.prompts import SUMMARY_GENERATOR_SYSTEM, SUMMARY_GENERATOR_USER_TEMPLATE
from ai_agent.reference_scorer import call_ollama_json

def compute_composite_score(app: dict) -> dict:
    """
    Takes an application dict with all AI scores populated.
    Computes the weighted composite score (0-100).
    """
    w = SCORING_WEIGHTS
    
    # Income score is already 0-100 from income_checker
    income_score = app.get("income_score", 0)
    
    # Reference scores are 1-10; normalise to 0-100
    employer_ref_score = app.get("employer_ref_score", 5) * 10
    landlord_ref_score = app.get("landlord_ref_score", 5) * 10
    
    # Cover letter score is 1-10; normalise to 0-100
    cover_letter_score = app.get("cover_letter_score", 5) * 10
    
    # Document completeness: 100 if all docs present, reduce by 10 per missing
    missing_count = len(app.get("missing_docs", []))
    doc_completeness_score = max(0, 100 - (missing_count * 10))
    
    # Inconsistency penalty: Low=0, Medium=15, High=35 points deducted from 100
    risk_level = app.get("inconsistency_risk", "Low")
    inconsistency_base = {"Low": 100, "Medium": 70, "High": 40}.get(risk_level, 100)
    
    # Apply income discrepancy penalty if found
    if app.get("income_discrepancy"):
        discrepancy_pct = app["income_discrepancy"].get("difference_pct", 0)
        if discrepancy_pct > 10:
            inconsistency_base = min(inconsistency_base, 60)
    
    # Weighted composite
    composite = (
        income_score           * w["income_score"] +
        employer_ref_score     * w["employer_reference"] +
        landlord_ref_score     * w["landlord_reference"] +
        cover_letter_score     * w["cover_letter"] +
        inconsistency_base     * w["inconsistency_penalty"] +
        doc_completeness_score * w["document_completeness"]
    )
    
    app["composite_score"] = round(composite, 1)
    app["score_breakdown"] = {
        "income_score": income_score,
        "employer_ref_score_normalised": employer_ref_score,
        "landlord_ref_score_normalised": landlord_ref_score,
        "cover_letter_score_normalised": cover_letter_score,
        "doc_completeness_score": doc_completeness_score,
        "inconsistency_base_score": inconsistency_base,
    }
    
    # AI Task: Suggest alternative properties if score is high
    from ai_agent.matcher import find_best_fit_properties
    app["alternative_properties"] = find_best_fit_properties(app, app["composite_score"])
    
    # Generate summary after scoring
    generate_summary(app)
    
    return app

from rpa.property_manager import get_property

def generate_summary(app: dict):
    """Generates the final AI summary and recommendation."""
    prop = get_property(app.get("property_id", "PROP-001"))
    if not prop:
        prop = {
            "address": "Unknown Property",
            "rent": "0",
            "requirements": "No requirements specified",
            "landlord_note": ""
        }
    
    prop_str = f"Address: {prop['address']}, Rent: €{prop['rent']}, Requirements: {prop['requirements']}"
    
    user_prompt = SUMMARY_GENERATOR_USER_TEMPLATE.format(
        applicant_name=app["applicant_name"],
        ref_number=app["ref_number"],
        property_address=prop["address"],
        property_rent=prop["rent"],
        income_ratio=app.get("income_ratio", 0),
        income_score=app.get("income_score", 0),
        employer_ref_score=app.get("employer_ref_score", 0),
        landlord_ref_score=app.get("landlord_ref_score", 0),
        cover_letter_score=app.get("cover_letter_score", 0),
        inconsistency_risk=app.get("inconsistency_risk", "Low"),
        inconsistency_count=len(app.get("inconsistency_findings", [])),
        composite_score=app.get("composite_score", 0),
        ref_red_flags=", ".join(app.get("red_flags", [])),
        cover_letter_concerns=", ".join(app.get("cover_letter_concerns", [])),
        inconsistency_findings=str(app.get("inconsistency_findings", [])),
        income_discrepancy=str(app.get("income_discrepancy", "None"))
    )
    
    system_prompt = SUMMARY_GENERATOR_SYSTEM.format(property_details=prop_str)
    
    if OLLAMA_MODEL == "mock":
        app["recommendation"] = "Strong Candidate" if app["composite_score"] > 85 else "Good Candidate"
        app["ai_summary"] = f"Mock summary for {app['applicant_name']}. Composite score {app['composite_score']}."
        app["action_required"] = "None"
        app["invite_to_viewing"] = app["composite_score"] > 80
        return

    try:
        result = call_ollama_json(system_prompt, user_prompt)
        app["recommendation"] = result.get("recommendation", "Review required")
        app["ai_summary"] = result.get("summary", "No summary generated.")
        app["detailed_reasoning"] = result.get("detailed_reasoning", "No detailed reasoning provided.")
        app["transparency_note"] = result.get("transparency_note", "No transparency note provided.")
        app["action_required"] = result.get("action_required", "None")
        app["invite_to_viewing"] = result.get("invite_to_viewing", False)
    except Exception as e:
        print(f"  [AI ERROR] {app['ref_number']} summary: {e}")
        app["recommendation"] = "Error"
        app["ai_summary"] = f"Error generating summary: {str(e)}"

def save_individual_report(app: dict):
    """Saves JSON and human-readable TXT report for one applicant."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ref = app["ref_number"]
    
    # JSON report (machine-readable, used by Streamlit UI)
    json_path = REPORTS_DIR / f"{ref}_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(app, f, indent=2, default=str)
    
    # TXT report (human-readable for letting agent)
    txt_path = REPORTS_DIR / f"{ref}_report.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"DRAP APPLICANT REPORT\n")
        f.write(f"{'='*60}\n")
        f.write(f"Reference: {ref}\n")
        f.write(f"Applicant: {app.get('applicant_name', 'Unknown')}\n")
        f.write(f"Status: {app.get('status', 'Unknown')}\n")
        f.write(f"\nCOMPOSITE SCORE: {app.get('composite_score', 'N/A')}/100\n")
        f.write(f"RECOMMENDATION: {app.get('recommendation', 'Review required')}\n")
        f.write(f"\nSCORE BREAKDOWN:\n")
        for key, val in app.get("score_breakdown", {}).items():
            f.write(f"  {key}: {val}\n")
        f.write(f"\nAI SUMMARY:\n{app.get('ai_summary', 'Not generated')}\n")
        f.write(f"\nACTION REQUIRED: {app.get('action_required', 'None')}\n")
        if app.get("red_flags"):
            f.write(f"\nRED FLAGS:\n")
            for flag in app["red_flags"]:
                f.write(f"  [!] {flag}\n")
    
    print(f"  [REPORT] {ref}: Saved report (score: {app.get('composite_score')}/100)")


def generate_ranked_shortlist(applications: list[dict]):
    """Generates shortlist_ranked.csv sorted by composite score."""
    import csv
    
    # Only include scored applications
    scored = [a for a in applications if "composite_score" in a]
    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(SHORTLIST_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "rank", "ref_number", "applicant_name", "composite_score",
            "income_ratio", "recommendation", "action_required",
            "invite_to_viewing", "status"
        ])
        for rank, app in enumerate(scored, 1):
            writer.writerow([
                rank,
                app.get("ref_number"),
                app.get("applicant_name"),
                app.get("composite_score"),
                app.get("income_ratio"),
                app.get("recommendation"),
                app.get("action_required"),
                app.get("invite_to_viewing"),
                app.get("status"),
            ])
    
    print(f"\n[SHORTLIST] Ranked shortlist written to {SHORTLIST_PATH}")
    print(f"[SHORTLIST] Top 5 applicants:")
    for rank, app in enumerate(scored[:5], 1):
        print(f"  #{rank}: {app.get('applicant_name')} - {app.get('composite_score')}/100 - {app.get('recommendation')}")
