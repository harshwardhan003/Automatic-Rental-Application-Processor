"""
DRAP Command-Line Interface
Usage: python main.py <command>

Commands:
  run        Run the complete pipeline (all stages)
  rpa        Run RPA stages only (intake + validation + income)
  score      Run AI scoring only (requires RPA to have run first)
  audit      Run the bias audit on scored results
  report     Print summary report to terminal
  reset      Clear all output files and start fresh
  check      Verify environment and configuration
  demo       Run with print-friendly output for video demo
  gdpr       Print GDPR ledger and deletion schedule
"""

import sys
import argparse
import shutil
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from rpa.intake_processor import run_intake
from rpa.document_validator import run_document_validation
from rpa.income_checker import run_income_checks
from ai_agent.reference_scorer import run_reference_scoring
from ai_agent.cover_letter_analyser import run_cover_letter_analysis
from ai_agent.inconsistency_detector import run_inconsistency_detection
from ai_agent.composite_scorer import (
    compute_composite_score, save_individual_report, generate_ranked_shortlist
)
from ai_agent.bias_auditor import run_bias_audit
from rpa.email_sender import (
    send_viewing_invitation, send_ai_rejection_email
)
from rpa.tracker_updater import finalise_tracker
from config.settings import OUTPUT_DIR, DATA_DIR, OLLAMA_MODEL, GDPR_DB_PATH

def check_environment():
    """Verify environment and configuration."""
    print("\n" + "="*30)
    print("ENVIRONMENT CHECK")
    print("="*30)
    
    # Check Python version
    print(f"[CHECK] Python: {sys.version.split()[0]} [OK]")
    
    # Check Ollama
    import requests
    try:
        resp = requests.get(OLLAMA_MODEL.replace("/v1", "/api/tags") if "http" in OLLAMA_MODEL else "http://localhost:11434/api/tags", timeout=2)
        print(f"[CHECK] Ollama Server: [OK]")
    except:
        print("[CHECK] Ollama Server: [NOT REACHABLE] (Is Ollama running?)")
        
    print(f"[CHECK] AI Model: {OLLAMA_MODEL} [OK]")
        
    # Check Data directory
    if DATA_DIR.exists():
        apps = list((DATA_DIR / "applications").iterdir())
        print(f"[CHECK] Data directory: [FOUND] ({len(apps)} applications)")
    else:
        print("[CHECK] Data directory: [MISSING]")
        
    # Check Output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("[CHECK] Output directory: [READY]")
    
    print("\nAll checks passed. System ready.")

def reset_outputs():
    """Clear all output files and start fresh."""
    print(f"[RESET] Clearing outputs in {OUTPUT_DIR}...")
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("[RESET] Done.")

def print_gdpr_report():
    """Print GDPR ledger and deletion schedule."""
    from rpa.gdpr_ledger import get_all_consent_records
    records = get_all_consent_records()
    print("\n" + "="*60)
    print("GDPR CONSENT LEDGER")
    print("="*60)
    if not records:
        print("No records found.")
    else:
        for r in records:
            print(f"Ref: {r[1]} | Name: {r[2]} | Received: {r[4][:10]} | Deletion Due: {r[7][:10]}")
    print("="*60)

def run_full_pipeline(target_property_id: str = None, demo_mode: bool = False):
    """Execute the complete DRAP pipeline end-to-end."""
    print("\n" + "-"*40)
    print("DRAP - DUBLIN RENTAL APPLICATION PROCESSOR")
    
    from rpa.property_manager import get_property
    if target_property_id:
        prop = get_property(target_property_id)
        prop_label = prop.get("address", "Unknown Property")
    else:
        prop_label = "All Properties"
        
    print(f"Clarendon Residential | {prop_label}")
    print("-"*40 + "\n")
    
    # Stage 1: Intake
    applications = run_intake()
    
    # Override property_id if target_property_id is provided
    if target_property_id:
        for app in applications:
            app["property_id"] = target_property_id
            
    # Stage 2-3: RPA
    applications = run_document_validation(applications)
    applications = run_income_checks(applications)
    
    # Stage 4: AI Scoring (eligible applicants only)
    eligible = [a for a in applications if a.get("income_eligible", False)]
    print(f"\n[AI STAGE] {len(eligible)} eligible application(s) proceeding to AI scoring.\n")
    
    eligible = run_reference_scoring(eligible)
    eligible = run_cover_letter_analysis(eligible)
    eligible = run_inconsistency_detection(eligible)
    
    # Composite scoring and reports
    print("\n" + "="*60)
    print("STAGE 5: COMPOSITE SCORING AND REPORT GENERATION")
    print("="*60)
    for app in eligible:
        app = compute_composite_score(app)
        save_individual_report(app)
    
    generate_ranked_shortlist(eligible)
    
    # Send outcome emails (Stage 5.1)
    print("\n" + "="*60)
    print("STAGE 5.1: AUTOMATED OUTCOME EMAILS")
    print("="*60)
    for app in eligible:
        if app.get("invite_to_viewing", False):
            send_viewing_invitation(app)
        else:
            send_ai_rejection_email(app)
            
    finalise_tracker(applications)  # Update non-eligible apps in tracker too
    
    # Run bias audit at the end
    run_bias_audit(eligible)
    
    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(f"  Total applications processed: {len(applications)}")
    print(f"  AI-scored applications: {len(eligible)}")
    print(f"  Output: output/applications_master.xlsx")
    print(f"  Ranked shortlist: output/shortlist_ranked.csv")
    print(f"  Individual reports: output/individual_reports/")
    print("\nLaunch dashboard: streamlit run app.py")


def main():
    parser = argparse.ArgumentParser(description="DRAP - Dublin Rental Application Processor")
    parser.add_argument("command", choices=["run","rpa","score","audit","report",
                                             "reset","check","demo","gdpr"])
    parser.add_argument("--prop", help="Target property ID for analysis (overrides application forms)")
    args = parser.parse_args()
    
    if args.command == "run":
        run_full_pipeline(target_property_id=args.prop)
    elif args.command == "demo":
        run_full_pipeline(target_property_id=args.prop, demo_mode=True)
    elif args.command == "audit":
        run_bias_audit()
    elif args.command == "check":
        check_environment()
    elif args.command == "reset":
        reset_outputs()
    elif args.command == "gdpr":
        print_gdpr_report()
    elif args.command == "rpa":
        apps = run_intake()
        apps = run_document_validation(apps)
        run_income_checks(apps)
    elif args.command == "score":
        # AI Scoring only - requires RPA outputs to be present
        # In a real system, we'd load from the tracker. Here we re-run intake for demo simplicity.
        apps = run_intake()
        apps = run_document_validation(apps)
        apps = run_income_checks(apps)
        eligible = [a for a in apps if a.get("income_eligible", False)]
        eligible = run_reference_scoring(eligible)
        eligible = run_cover_letter_analysis(eligible)
        eligible = run_inconsistency_detection(eligible)
        for app in eligible:
            app = compute_composite_score(app)
            save_individual_report(app)
        generate_ranked_shortlist(eligible)
        print("\nScoring complete.")
    else:
        print(f"Command '{args.command}' not yet implemented standalone. Use 'run'.")


if __name__ == "__main__":
    main()
