"""
RPA Module: GDPR Ledger
Handles the SQLite database for consent logging and data retention.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from config.settings import GDPR_DB_PATH, GDPR_DATA_RETENTION_DAYS, get_gdpr_purpose

def log_consent_receipt(ref_number: str, applicant_name: str, applicant_email: str, received_at: str, property_address: str = None):
    """Logs a new consent record in the SQLite database."""
    conn = sqlite3.connect(GDPR_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS consent_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ref_number TEXT NOT NULL,
        applicant_name TEXT,
        applicant_email TEXT,
        received_at TEXT,
        processing_purpose TEXT,
        automated_processing_disclosed TEXT DEFAULT 'Yes',
        deletion_scheduled_at TEXT,
        actual_deleted_at TEXT,
        status TEXT DEFAULT 'Active'
    )
    """)
    
    # Calculate deletion date (90 days from received)
    received_dt = datetime.fromisoformat(received_at)
    deletion_dt = received_dt + timedelta(days=GDPR_DATA_RETENTION_DAYS)
    
    purpose = get_gdpr_purpose(property_address) if property_address else get_gdpr_purpose()
    
    cursor.execute("""
    INSERT INTO consent_log 
    (ref_number, applicant_name, applicant_email, received_at, processing_purpose, deletion_scheduled_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (ref_number, applicant_name, applicant_email, received_at, purpose, deletion_dt.isoformat()))
    
    conn.commit()
    conn.close()
    print(f"  [GDPR] Logged consent for {ref_number}")

def get_all_consent_records():
    """Returns all records from the consent log."""
    if not GDPR_DB_PATH.exists():
        return []
    conn = sqlite3.connect(GDPR_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM consent_log")
    records = cursor.fetchall()
    conn.close()
    return records
