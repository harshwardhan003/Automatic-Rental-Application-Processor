"""
RPA Module: Email Sender
Handles outbound communication with applicants.
In simulation mode, it writes emails to output/email_log.csv.
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path
from config.settings import EMAIL_LOG_PATH, EMAIL_SIMULATION_MODE, RESUBMISSION_WINDOW_HOURS
from rpa.email_templates import (
    MISSING_DOCS_TEMPLATE, INCOME_REJECTION_TEMPLATE, ACKNOWLEDGEMENT_TEMPLATE,
    VIEWING_INVITATION_TEMPLATE, AI_REJECTION_TEMPLATE
)

def get_missing_docs_draft(app: dict) -> str:
    deadline = datetime.now() + timedelta(hours=RESUBMISSION_WINDOW_HOURS)
    return MISSING_DOCS_TEMPLATE.format(
        ref_number=app["ref_number"],
        applicant_name=app["applicant_name"],
        property_address=app.get("property_address", "the property"),
        missing_docs_list="\n".join([f"- {d}" for d in app.get("missing_docs", [])]),
        deadline_datetime=deadline.strftime("%Y-%m-%d %H:%M")
    )

def get_income_rejection_draft(app: dict, ratio: float = 0.0, monthly_rent: float = 2000.0) -> str:
    required_income = monthly_rent * 3.0
    return INCOME_REJECTION_TEMPLATE.format(
        ref_number=app["ref_number"],
        applicant_name=app["applicant_name"],
        property_address=app.get("property_address", "the property"),
        required_income=required_income
    )

def get_viewing_invitation_draft(app: dict) -> str:
    return VIEWING_INVITATION_TEMPLATE.format(
        ref_number=app["ref_number"],
        applicant_name=app["applicant_name"],
        property_address=app.get("property_address", "the property"),
        transparency_note=app.get("transparency_note", "Strong overall application profile.")
    )

def get_ai_rejection_draft(app: dict) -> str:
    return AI_REJECTION_TEMPLATE.format(
        ref_number=app["ref_number"],
        applicant_name=app["applicant_name"],
        property_address=app.get("property_address", "the property"),
        transparency_note=app.get("transparency_note", "Did not meet the threshold for this property's specific requirements.")
    )

def log_email(ref_number: str, recipient_email: str, email_type: str, subject: str):
    """Logs the sent email to a CSV file."""
    file_exists = EMAIL_LOG_PATH.exists()
    with open(EMAIL_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "ref_number", "recipient_email", "email_type", "status", "subject"])
        writer.writerow([datetime.now().isoformat(), ref_number, recipient_email, email_type, "Sent", subject])

def send_missing_documents_email(app: dict):
    """Simulates sending an email about missing documents."""
    deadline = datetime.now() + timedelta(hours=RESUBMISSION_WINDOW_HOURS)
    content = MISSING_DOCS_TEMPLATE.format(
        ref_number=app["ref_number"],
        applicant_name=app["applicant_name"],
        property_address=app.get("property_address", "the property"),
        missing_docs_list="\n".join([f"- {d}" for d in app.get("missing_docs", [])]),
        deadline_datetime=deadline.strftime("%Y-%m-%d %H:%M")
    )
    subject = content.splitlines()[0].replace("Subject: ", "")
    
    if EMAIL_SIMULATION_MODE:
        print(f"  [EMAIL SIMULATION] Sent Missing Docs email to {app.get('applicant_email', 'unknown@example.com')}")
        log_email(app["ref_number"], app.get("applicant_email", "unknown@example.com"), "Missing Documents", subject)
    else:
        pass

def send_income_rejection_email(app: dict, ratio: float, monthly_rent: float):
    """Simulates sending an income rejection email."""
    content = INCOME_REJECTION_TEMPLATE.format(
        ref_number=app["ref_number"],
        applicant_name=app["applicant_name"],
        property_address=app.get("property_address", "the property"),
        required_income=monthly_rent * 3.0
    )
    subject = content.splitlines()[0].replace("Subject: ", "")
    
    if EMAIL_SIMULATION_MODE:
        print(f"  [EMAIL SIMULATION] Sent Income Rejection email to {app.get('applicant_email', 'unknown@example.com')}")
        log_email(app["ref_number"], app.get("applicant_email", "unknown@example.com"), "Income Rejection", subject)
    else:
        pass

def send_viewing_invitation(app: dict):
    """Simulates sending a viewing invitation."""
    content = VIEWING_INVITATION_TEMPLATE.format(
        ref_number=app["ref_number"],
        applicant_name=app["applicant_name"],
        property_address=app.get("property_address", "the property"),
        transparency_note=app.get("transparency_note", "Strong overall application profile.")
    )
    subject = content.splitlines()[0].replace("Subject: ", "")
    
    if EMAIL_SIMULATION_MODE:
        print(f"  [EMAIL SIMULATION] Sent Viewing Invitation to {app.get('applicant_email', 'unknown@example.com')}")
        log_email(app["ref_number"], app.get("applicant_email", "unknown@example.com"), "Viewing Invitation", subject)

def send_ai_rejection_email(app: dict):
    """Simulates sending an AI-based rejection email with reasons."""
    content = AI_REJECTION_TEMPLATE.format(
        ref_number=app["ref_number"],
        applicant_name=app["applicant_name"],
        property_address=app.get("property_address", "the property"),
        transparency_note=app.get("transparency_note", "Did not meet the threshold for this property's specific requirements.")
    )
    subject = content.splitlines()[0].replace("Subject: ", "")
    
    if EMAIL_SIMULATION_MODE:
        print(f"  [EMAIL SIMULATION] Sent AI Rejection to {app.get('applicant_email', 'unknown@example.com')}")
        log_email(app["ref_number"], app.get("applicant_email", "unknown@example.com"), "AI Rejection", subject)

def send_acknowledgement_email(app: dict):
    """Simulates sending an acknowledgement email."""
    content = ACKNOWLEDGEMENT_TEMPLATE.format(
        ref_number=app["ref_number"],
        applicant_name=app["applicant_name"],
        property_address=app.get("property_address", "the property")
    )
    subject = content.splitlines()[0].replace("Subject: ", "")
    
    if EMAIL_SIMULATION_MODE:
        print(f"  [EMAIL SIMULATION] Sent Acknowledgement email to {app.get('applicant_email', 'unknown@example.com')}")
        log_email(app["ref_number"], app.get("applicant_email", "unknown@example.com"), "Acknowledgement", subject)
    else:
        pass
