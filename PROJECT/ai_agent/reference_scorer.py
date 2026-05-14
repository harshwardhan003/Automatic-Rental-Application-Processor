"""
AI Agent Module 1: Reference Scorer
Evaluates employer and landlord reference letters using LOCAL OLLAMA.
Supports multi-property context.
"""

import json
import csv
from pathlib import Path
from openai import OpenAI
from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL, AI_MAX_TOKENS, PROPERTIES_PATH
from ai_agent.prompts import REFERENCE_SCORER_SYSTEM, REFERENCE_SCORER_USER_TEMPLATE

def get_property_details(property_id: str) -> dict:
    """Loads property details from properties.csv."""
    if not PROPERTIES_PATH.exists():
        return {"address": "Unknown Dublin Property", "rent": 2000, "requirements": "Standard"}
    
    with open(PROPERTIES_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["property_id"] == property_id:
                return row
    return {"address": "Unknown Property", "rent": 2000, "requirements": "Standard"}

def call_ollama_json(system_prompt: str, user_prompt: str):
    """Utility to call local Ollama and parse JSON response."""
    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    
    # Inject property context into system prompt if markers exist
    # (Handling markers from prompts.py)
    
    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=AI_MAX_TOKENS,
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
        
    return json.loads(content)

def score_reference(app: dict, ref_type: str, prop: dict) -> dict:
    """Scores a single reference letter with property context."""
    folder = Path(app["folder_path"])
    file_map = {"employer": "employer_reference.txt", "landlord": "landlord_reference.txt"}
    ref_path = folder / file_map[ref_type]
    
    if not ref_path.exists():
        return {"score": 0, "red_flags": ["Missing reference"]}
    
    with open(ref_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    
    # Prepare dynamic prompts
    prop_str = f"Address: {prop['address']}, Rent: €{prop['rent']}, Requirements: {prop['requirements']}"
    
    system_prompt = REFERENCE_SCORER_SYSTEM.format(property_details=prop_str)
    user_prompt = REFERENCE_SCORER_USER_TEMPLATE.format(
        reference_type=ref_type,
        applicant_name=app["applicant_name"],
        ref_number=app["ref_number"],
        reference_text=text
    )
    
    try:
        if OLLAMA_MODEL == "mock":
            # Deterministic mock scores for testing
            mock_score = 8
            if "REF-2026-004" in app["ref_number"] and ref_type == "employer":
                mock_score = 6 # Emma Walsh has some instability
            elif "REF-2026-009" in app["ref_number"]:
                mock_score = 9 # Paul Mescal (demo data)
                
            return {
                "score": mock_score,
                "red_flags": [],
                "summary": f"Mock {ref_type} reference scoring."
            }

        result = call_ollama_json(system_prompt, user_prompt)
        return result
    except Exception as e:
        print(f"  [AI ERROR] {app['ref_number']} {ref_type} ref: {e}")
        return {"score": 5, "red_flags": [f"Scoring error: {str(e)}"]}

def run_reference_scoring(applications: list[dict]) -> list[dict]:
    """Runs reference scoring for all applicants in list."""
    print("\n" + "="*60)
    print("STAGE 4.1: REFERENCE SCORING (AI)")
    print("="*60)
    
    for app in applications:
        prop_id = app.get("property_id", "PROP-001")
        prop = get_property_details(prop_id)
        
        print(f"  [AI] Scoring references for {app['ref_number']} (Target: {prop['address']})...")
        emp_result = score_reference(app, "employer", prop)
        lan_result = score_reference(app, "landlord", prop)
        
        app["employer_ref_score"] = emp_result.get("score", 0)
        app["landlord_ref_score"] = lan_result.get("score", 0)
        app["red_flags"] = app.get("red_flags", []) + emp_result.get("red_flags", []) + lan_result.get("red_flags", [])
        
    return applications
