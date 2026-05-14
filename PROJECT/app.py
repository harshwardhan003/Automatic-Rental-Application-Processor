"""
DRAP Streamlit Web Application (Modern Dark Blue Edition)
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import json
import sqlite3
import csv
import io
import shutil
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import (
    OUTPUT_DIR, SHORTLIST_PATH, REPORTS_DIR, TRACKER_PATH,
    GDPR_DB_PATH, BIAS_AUDIT_PATH, EMAIL_LOG_PATH, DATA_DIR,
    APPLICATIONS_DIR, PROPERTIES_PATH
)

from rpa.property_manager import load_properties, add_property
from rpa.intake_processor import process_zip_upload
from rpa.email_sender import (
    send_viewing_invitation, send_ai_rejection_email,
    get_viewing_invitation_draft, get_ai_rejection_draft,
    get_missing_docs_draft, get_income_rejection_draft
)

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DRAP - Dublin Rental Application Processor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Midnight Blue Theme CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
    /* Global Background and Text */
    [data-testid="stAppViewContainer"] {
        background-color: #0f172a !important; 
    }
    p, span, label, li, h1, h2, h3, h4, h5, h6 {
        color: #f1f5f9 !important;
    }
    
    /* Header */
    [data-testid="stHeader"] {
        background-color: #0f172a !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
    }
    [data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
    }

    /* Cards and Metrics */
    .stMetric {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px;
        padding: 20px;
    }
    [data-testid="stMetricValue"] {
        color: #38bdf8 !important; 
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
    }

    /* Buttons */
    .stButton>button {
        background-color: #38bdf8 !important;
        color: #0f172a !important;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
    }

    /* Draft Terminal */
    .draft-terminal {
        background-color: #020617;
        color: #22c55e;
        padding: 20px;
        border-radius: 10px;
        font-family: 'Courier New', Courier, monospace;
        border: 1px solid #334155;
        white-space: pre-wrap;
    }

    /* Table Contrast */
    [data-testid="stTable"] {
        background-color: #1e293b !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── Navigation ───────────────────────────────────────────────────────────────
st.sidebar.title("Clarendon Residential")
st.sidebar.subheader("DRAP Intelligence Suite")
page = st.sidebar.radio("Navigation", [
    "System Dashboard",
    "Property Intelligence",
    "Application Hub",
    "Email Draft Terminal",
    "Applicant Analysis",
    "Property Manager"
])

# ─── Data Loading Helpers ──────────────────────────────────────────────────────

@st.cache_data(ttl=2)
def load_all_reports():
    reports = {}
    if REPORTS_DIR.exists():
        for f in REPORTS_DIR.glob("*.json"):
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
                reports[data.get("ref_number", f.stem)] = data
    return reports

@st.cache_data(ttl=2)
def load_tracker():
    if TRACKER_PATH.exists():
        return pd.read_excel(TRACKER_PATH)
    return pd.DataFrame()

# ─── PAGE: DASHBOARD ──────────────────────────────────────────────────────────

if page == "System Dashboard":
    st.title("DRAP Portfolio Dashboard")
    
    props = load_properties()
    tracker = load_tracker()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Properties", len(props))
    col2.metric("Total Applicants", len(tracker) if not tracker.empty else 0)
    
    eligible = 0
    if not tracker.empty:
        eligible = len(tracker[tracker["status"].str.contains("Eligible", na=False)])
    col3.metric("Eligible", eligible)
    
    scored = len(load_all_reports())
    col4.metric("AI Scored", scored)
    
    st.divider()
    st.subheader("Asset List")
    if props:
        st.dataframe(pd.DataFrame(props), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Pipeline Controls")
    
    prop_options = {p["address"]: p["property_id"] for p in props}
    selected_prop_addr = st.selectbox("Target Property for Analysis", list(prop_options.keys()))
    target_prop_id = prop_options[selected_prop_addr]
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Run Full Analysis Pipeline", type="primary"):
            with st.spinner("Analysing all applications..."):
                from main import run_full_pipeline
                run_full_pipeline(target_property_id=target_prop_id)
                st.cache_data.clear()
            st.success("Analysis complete. Data refreshed.")
            st.rerun()
    with col2:
        if st.button("Reset All Data (Clear Cache)"):
            st.cache_data.clear()
            st.success("Cache cleared.")
            st.rerun()

# ─── PAGE: PROPERTY INTELLIGENCE ──────────────────────────────────────────────

elif page == "Property Intelligence":
    st.title("Property Matching Intelligence")
    st.write("Match applicants to properties based on scores and preferences.")
    
    props = load_properties()
    reports = load_all_reports()
    
    if not props:
        st.warning("No properties found.")
    else:
        prop_options = {p["address"]: p for p in props}
        selected_addr = st.selectbox("Select Property to Optimize", list(prop_options.keys()))
        target_prop = prop_options[selected_addr]
        
        st.subheader(f"Best Candidates for: {selected_addr}")
        
        # We consider ALL high-scoring applicants, regardless of which property they originally applied for
        all_candidates = []
        for app in reports.values():
            income = app.get("authoritative_income", 0)
            rent = float(target_prop["rent"])
            
            # Recompute income score for this specific property
            income_ratio = income / rent if rent > 0 else 0
            if income_ratio >= 4.0:
                dynamic_income_score = 100
            elif income_ratio >= 3.0:
                dynamic_income_score = 60 + int((income_ratio - 3.0) / 1.0 * 40)
            else:
                dynamic_income_score = int(income_ratio / 3.0 * 60)
            
            # Basic filters: income must be sufficient
            if income_ratio >= 2.75:
                # Calculate "Match Score" using dynamic income score
                # Base match is weighted: 40% dynamic income, 60% other factors from original score
                # (since original score is 25% income, we replace that component)
                base_other_score = app.get("composite_score", 0) - (app.get("income_score", 0) * 0.25)
                match_score = base_other_score + (dynamic_income_score * 0.25)
                
                prefs = app.get("preferences", {})
                if prefs.get("area", "").lower() in target_prop["address"].lower():
                    match_score += 10 # Preference bonus
                if int(target_prop["beds"]) >= int(prefs.get("beds", 1)):
                    match_score += 5 # Bed bonus
                
                all_candidates.append({
                    "Name": app["applicant_name"],
                    "Base Score": app.get("composite_score", 0),
                    "Intelligence Match": round(min(100, match_score), 1),
                    "Original Target": app["property_id"],
                    "Income Coverage": f"{income_ratio:.2f}x",
                    "Details": app.get("ai_summary", "N/A")
                })
        
        if not all_candidates:
            st.info("No candidates meet the financial criteria for this property.")
        else:
            all_candidates.sort(key=lambda x: x["Intelligence Match"], reverse=True)
            top_3 = all_candidates[:3]
            
            for i, cand in enumerate(top_3, 1):
                with st.expander(f"Rank #{i}: {cand['Name']} (Match: {cand['Intelligence Match']}/100)"):
                    st.write(f"**Original Application:** {cand['Original Target']}")
                    st.write(f"**Income Coverage for this unit:** {cand['Income Coverage']}")
                    st.info(cand['Details'])

# ─── PAGE: EMAIL DRAFT TERMINAL ───────────────────────────────────────────────

elif page == "Email Draft Terminal":
    st.title("Property-Specific Draft Terminal")
    
    reports = load_all_reports()
    props = load_properties()
    
    if not reports:
        st.warning("No processed applications.")
    else:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            selected_ref = st.selectbox("Select Applicant", sorted(reports.keys()))
            app = reports[selected_ref]
            
            prop_options = {p["address"]: p for p in props}
            selected_prop_addr = st.selectbox("Draft for Property", list(prop_options.keys()), index=0)
            target_prop = prop_options[selected_prop_addr]
            
            # Temporary context update for the draft
            app_context = app.copy()
            app_context["property_id"] = target_prop["property_id"]
            app_context["property_address"] = target_prop["address"]
            
            # Recalculate income coverage for this specific property
            try:
                monthly_rent = float(target_prop.get("rent", 2000))
                income = float(app.get("authoritative_income", 0))
                ratio = income / monthly_rent
                app_context["income_ratio"] = round(ratio, 2)
                
                # Update transparency note if it's a rejection based on this specific property's income
                if ratio < 3.0:
                    app_context["transparency_note"] = f"Monthly income of €{income:,.0f} does not meet the 3x rent coverage requirement for this property (Rent: €{monthly_rent:,.0f})."
            except:
                pass
            
            draft_type = st.radio("Message Context", ["Invitation", "Rejection", "Income Rejection", "Missing Docs"])
            
        with col2:
            st.write(f"**Drafting for:** {app['applicant_name']} @ {target_prop['address']}")
            
            draft_content = ""
            if draft_type == "Invitation":
                draft_content = get_viewing_invitation_draft(app_context)
            elif draft_type == "Rejection":
                draft_content = get_ai_rejection_draft(app_context)
            elif draft_type == "Income Rejection":
                rent = float(target_prop.get("rent", 2000))
                draft_content = get_income_rejection_draft(app_context, ratio=app_context.get("income_ratio", 0), monthly_rent=rent)
            elif draft_type == "Missing Docs":
                draft_content = get_missing_docs_draft(app_context)
                
            st.markdown(f'<div class="draft-terminal">{draft_content}</div>', unsafe_allow_html=True)

            st.divider()
            if st.button("Send This Email", type="primary"):
                try:
                    if draft_type == "Invitation":
                        send_viewing_invitation(app_context)
                    elif draft_type == "Rejection":
                        send_ai_rejection_email(app_context)
                    elif draft_type == "Income Rejection":
                        rent = float(target_prop.get("rent", 2000))
                        send_income_rejection_email(app_context, app_context.get("income_ratio", 0), rent)
                    elif draft_type == "Missing Docs":
                        send_missing_documents_email(app_context)
                    
                    st.success(f"Email sent to {app_context.get('applicant_email')}")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Failed to send email: {e}")

# ─── PAGE: APPLICANT ANALYSIS ─────────────────────────────────────────────────

elif page == "Applicant Analysis":
    st.title("Deep Analysis")
    reports = load_all_reports()
    
    if not reports:
        st.warning("No data.")
    else:
        selected_ref = st.selectbox("Select Candidate", sorted(reports.keys()))
        app = reports[selected_ref]
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric("Score", f"{app['composite_score']}/100")
            st.write(f"**Target:** {app['property_id']}")
            st.write(f"**Income:** €{app.get('authoritative_income', 0):,.0f}")
            st.write("**Preferences:**")
            st.json(app.get("preferences", {}))
        
        with col2:
            st.subheader("Assessment Narrative")
            st.info(app.get("ai_summary", "N/A"))
            st.write(app.get("detailed_reasoning", "N/A"))

# ─── PAGE: APPLICATION HUB ────────────────────────────────────────────────────

elif page == "Application Hub":
    st.title("Intake Hub")
    uploaded_file = st.file_uploader("Upload Application ZIP", type="zip")
    if uploaded_file and st.button("Execute Intake"):
        temp_zip = Path("data/temp_upload.zip")
        with open(temp_zip, "wb") as f: f.write(uploaded_file.getbuffer())
        process_zip_upload(temp_zip)
        st.success("Intake Success.")
        temp_zip.unlink()

# ─── PAGE: PROPERTY MANAGER ──────────────────────────────────────────────────

elif page == "Property Manager":
    st.title("Asset Manager")
    tab1, tab2 = st.tabs(["List", "Register"])
    with tab1:
        st.table(load_properties())
    with tab2:
        with st.form("new_prop"):
            p_id = st.text_input("ID")
            p_addr = st.text_input("Address")
            p_rent = st.number_input("Rent", min_value=500)
            p_beds = st.number_input("Beds", min_value=1)
            if st.form_submit_button("Save"):
                add_property({"property_id":p_id, "address":p_addr, "rent":p_rent, "beds":p_beds, "requirements":"", "landlord_note":""})
                st.cache_data.clear()
                st.success("Saved.")
                st.rerun()
