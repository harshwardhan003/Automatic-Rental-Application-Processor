"""
RPA Module 2: Document Completeness Validator
Checks each application folder for all required documents.
Fires email for missing documents. Updates tracker.
"""

import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import REQUIRED_DOCUMENTS, APPLICATIONS_DIR
from rpa.tracker_updater import update_application_status, update_document_flags
from rpa.email_sender import send_missing_documents_email


def validate_application(app: dict) -> dict:
    """
    Checks whether all required documents are present and non-empty
    for a single application. Returns the app dict updated with validation results.
    """
    folder = Path(app["folder_path"])
    missing_docs = []
    doc_status = {}
    
    for doc_name in REQUIRED_DOCUMENTS:
        doc_path = folder / doc_name
        if not doc_path.exists():
            missing_docs.append(doc_name)
            doc_status[doc_name] = "MISSING"
        elif doc_path.stat().st_size == 0:
            missing_docs.append(doc_name)
            doc_status[doc_name] = "EMPTY"
        else:
            doc_status[doc_name] = "PRESENT"
    
    app["doc_status"] = doc_status
    app["missing_docs"] = missing_docs
    app["doc_check_passed"] = len(missing_docs) == 0
    
    if app["doc_check_passed"]:
        app["status"] = "Complete"
        print(f"  [DOC CHECK] {app['ref_number']} [OK] All documents present")
    else:
        app["status"] = "Incomplete - Missing Documents"
        missing_list = ", ".join(missing_docs)
        print(f"  [DOC CHECK] {app['ref_number']} [FAIL] Missing: {missing_list}")
        send_missing_documents_email(app)
    
    update_document_flags(app["ref_number"], doc_status)
    update_application_status(app["ref_number"], app["status"])
    return app


def run_document_validation(applications: list[dict]) -> list[dict]:
    """Validates all applications. Returns list with updated statuses."""
    print("\n" + "="*60)
    print("STAGE 2: DOCUMENT VALIDATION (RPA)")
    print("="*60)
    
    validated = []
    for app in applications:
        validated.append(validate_application(app))
    
    passed = sum(1 for a in validated if a["doc_check_passed"])
    failed = len(validated) - passed
    print(f"\n[DOC VALIDATION] Complete. {passed} passed, {failed} require resubmission.\n")
    return validated
