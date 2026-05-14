"""
RPA Module 1: Application Intake Processor
Scans the applications directory, registers each submission,
assigns reference numbers, and initialises tracking.
"""

import os
import csv
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import (
    APPLICATIONS_DIR, TRACKER_PATH, OUTPUT_DIR,
    REPORTS_DIR, EMAIL_LOG_PATH
)
from rpa.tracker_updater import initialise_tracker, add_application_row, get_existing_refs
from rpa.gdpr_ledger import log_consent_receipt

def process_zip_upload(zip_file_path: Path) -> list[dict]:
    """
    RPA Task: Extracts a ZIP file containing multiple application folders
    and registers them.
    """
    print(f"[RPA INTAKE] Processing ZIP upload: {zip_file_path.name}")
    extraction_dir = APPLICATIONS_DIR
    extraction_dir.mkdir(parents=True, exist_ok=True)
    
    new_apps = []
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        # Get list of top-level directories in ZIP
        top_level = {Path(n).parts[0] for n in zip_ref.namelist() if "/" in n}
        
        for folder_name in top_level:
            if folder_name.startswith("REF-"):
                zip_ref.extractall(extraction_dir, members=[
                    m for m in zip_ref.namelist() if m.startswith(folder_name)
                ])
                print(f"  [RPA] Extracted application: {folder_name}")
                
                # Basic registration info
                app_path = extraction_dir / folder_name
                new_apps.append(scan_single_application(app_path))
                
    return register_applications(new_apps)

def scan_single_application(folder: Path) -> dict:
    """Scans a single application folder for metadata."""
    ref_number = folder.name.replace("_incomplete", "").replace("_flagged", "")
    form_path = folder / "application_form.csv"
    applicant_name = "Unknown"
    applicant_email = "Unknown"
    property_id = "PROP-001"
    consent_given = False
    preferences = {"area": "Dublin", "beds": 1}
    
    if form_path.exists():
        try:
            with open(form_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                data = {row["field"]: row["value"] for row in reader}
                applicant_name = data.get("full_name", "Unknown")
                applicant_email = data.get("email", "Unknown")
                property_id = data.get("property_id", "PROP-001")
                consent_given = data.get("consent_gdpr", "No").lower() == "yes"
                
                # Add preferences if available
                preferences["area"] = data.get("preferred_area", "Dublin")
                preferences["beds"] = int(data.get("preferred_beds", 1))
        except Exception as e:
            print(f"  [RPA ERROR] Could not read form for {ref_number}: {e}")
            
    return {
        "ref_number": ref_number,
        "property_id": property_id,
        "folder_path": str(folder),
        "folder_name": folder.name,
        "applicant_name": applicant_name,
        "applicant_email": applicant_email,
        "consent_given": consent_given,
        "preferences": preferences,
        "received_at": datetime.now().isoformat(),
        "status": "Received",
    }

def scan_applications() -> list[dict]:
    """
    Scans the applications directory for all REF-XXXX folders.
    Returns a list of dicts with basic metadata for each application found.
    """
    applications = []
    
    if not APPLICATIONS_DIR.exists():
        APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
        return []
    
    for folder in sorted(APPLICATIONS_DIR.iterdir()):
        if folder.is_dir() and folder.name.startswith("REF-"):
            applications.append(scan_single_application(folder))
    
    print(f"[INTAKE] Found {len(applications)} application(s) in storage.")
    return applications


def register_applications(applications: list[dict]) -> list[dict]:
    """
    Registers each application in the master tracker and GDPR ledger.
    Returns the same list with any additional fields added.
    """
    # Ensure output directories exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialise the Excel tracker if it doesn't exist
    initialise_tracker()
    
    # Initialise email log if it doesn't exist
    if not EMAIL_LOG_PATH.exists():
        with open(EMAIL_LOG_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "ref_number", "recipient_email",
                             "email_type", "status", "subject"])
    
    from rpa.property_manager import get_property
    
    existing_refs = get_existing_refs()
    
    for app in applications:
        if app["ref_number"] in existing_refs:
            print(f"[INTAKE] {app['ref_number']} already registered. Skipping.")
            continue
            
        print(f"[INTAKE] Registering {app['ref_number']} — {app['applicant_name']}")
        add_application_row(app)
        
        if app["consent_given"]:
            prop = get_property(app.get("property_id", "PROP-001"))
            prop_addr = prop.get("address")
            log_consent_receipt(
                ref_number=app["ref_number"],
                applicant_name=app["applicant_name"],
                applicant_email=app["applicant_email"],
                received_at=app["received_at"],
                property_address=prop_addr
            )
        else:
            print(f"[GDPR WARNING] {app['ref_number']}: No GDPR consent recorded in form.")
    
    return applications


def run_intake() -> list[dict]:
    """Main entry point for the intake stage."""
    print("\n" + "="*60)
    print("STAGE 1: APPLICATION INTAKE")
    print("="*60)
    applications = scan_applications()
    applications = register_applications(applications)
    print(f"[INTAKE] Complete. {len(applications)} application(s) registered.\n")
    return applications
