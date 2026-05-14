"""
AI Agent Module 5: Bias Auditor
Performs post-hoc fairness analysis on the scored dataset.
"""

import json
from pathlib import Path
from config.settings import BIAS_AUDIT_PATH, OLLAMA_MODEL
from ai_agent.prompts import BIAS_AUDITOR_SYSTEM, BIAS_AUDITOR_USER_TEMPLATE
from ai_agent.reference_scorer import call_ollama_json

def run_bias_audit(applications: list[dict] = None):
    """
    Runs the fairness audit. If applications list is not provided, 
    it should ideally load from the tracker or individual reports.
    """
    print("STAGE 6: BIAS AUDIT (AI)")

    
    if not applications:
        # Load from reports if not provided
        from config.settings import REPORTS_DIR
        applications = []
        for f in REPORTS_DIR.glob("*.json"):
            with open(f, encoding="utf-8") as fh:
                applications.append(json.load(fh))
    
    if not applications:
        print("[BIAS AUDIT] No scored applications found to audit.")
        return

    # Aggregate stats
    dataset_summary = f"Total audited: {len(applications)}\n"
    
    # Simple wordcount band analysis
    wc_stats = {"<80": [], "80-200": [], "200+": []}
    for app in applications:
        ref_path = Path(app["folder_path"]) / "cover_letter.txt"
        if ref_path.exists():
            wc = len(ref_path.read_text(encoding="utf-8", errors="replace").split())
            score = app.get("composite_score", 0)
            if wc < 80: wc_stats["<80"].append(score)
            elif wc <= 200: wc_stats["80-200"].append(score)
            else: wc_stats["200+"].append(score)
            
    # Simple name origin estimation (Irish vs Other)
    # This is a VERY crude mock for demonstration purposes
    name_stats = {"Irish-origin": [], "Other": []}
    irish_names = ["Niamh", "Ciarán", "Aoife", "Seán", "Sinéad", "Roisín", "Conor", "Méabh", "Tadhg", "Orlaith"]
    for app in applications:
        name = app.get("applicant_name", "")
        score = app.get("composite_score", 0)
        is_irish = any(iname in name for iname in irish_names)
        if is_irish: name_stats["Irish-origin"].append(score)
        else: name_stats["Other"].append(score)

    user_prompt = BIAS_AUDITOR_USER_TEMPLATE.format(
        dataset_summary=dataset_summary,
        wordcount_stats=str({k: sum(v)/len(v) if v else 0 for k, v in wc_stats.items()}),
        name_stats=str({k: sum(v)/len(v) if v else 0 for k, v in name_stats.items()})
    )
    
    if OLLAMA_MODEL == "mock":
        result = {
            "audit_conclusion": "No Concerns",
            "wordcount_correlation": "No significant correlation found in mock data.",
            "name_origin_finding": "No significant difference found in mock data.",
            "recommendations": ["Continue monitoring"],
            "audit_summary": "Mock bias audit complete. Dataset appears fair."
        }
    else:
        try:
            result = call_ollama_json(BIAS_AUDITOR_SYSTEM, user_prompt)

        except Exception as e:
            print(f"  [AI ERROR] Bias audit: {e}")
            result = {"audit_summary": f"Error during audit: {str(e)}"}

    with open(BIAS_AUDIT_PATH, "w", encoding="utf-8") as f:
        f.write("DRAP BIAS AUDIT REPORT\n")
        f.write(f"Conclusion: {result.get('audit_conclusion', 'N/A')}\n\n")
        f.write(f"Summary: {result.get('audit_summary', '')}\n\n")
        f.write(f"Wordcount Finding: {result.get('wordcount_correlation', '')}\n")
        f.write(f"Name Origin Finding: {result.get('name_origin_finding', '')}\n\n")
        f.write("Recommendations:\n")
        for rec in result.get("recommendations", []):
            f.write(f" - {rec}\n")
            
    print(f"[BIAS AUDIT] Complete. Report saved to {BIAS_AUDIT_PATH}")
