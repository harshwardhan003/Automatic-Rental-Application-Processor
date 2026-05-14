import os
import csv
import random
from pathlib import Path

DATA_DIR = Path("data/applications")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Extended applicant scenarios
applicant_base = [
    {"name": "Niamh Fitzgerald", "income": 7800, "scenario": "perfect"},
    {"name": "Ciarán Ryan", "income": 6500, "scenario": "low_income"},
    {"name": "Aoife Kelly", "income": 7200, "scenario": "vague_cover"},
    {"name": "Emma Walsh", "income": 6800, "scenario": "income_discrepancy"},
    {"name": "Liam Brennan", "income": 5500, "scenario": "ref_red_flags"},
    {"name": "Seán Doyle", "income": 7000, "scenario": "employment_gap"},
    {"name": "Claire Murphy", "income": 6000, "scenario": "low_income"},
    {"name": "Darragh O'Brien", "income": 7500, "scenario": "missing_docs"},
    {"name": "Sinéad Connolly", "income": 6800, "scenario": "perfect"},
    {"name": "Patrick Healy", "income": 6200, "scenario": "low_income"},
    {"name": "Roisín Ní Mhuirí", "income": 8000, "scenario": "self_employed"},
    {"name": "Conor MacGiolla", "income": 7200, "scenario": "high_income_bad_ref"},
    {"name": "Meabh de Búrca", "income": 7600, "scenario": "timeline_inconsistency"},
    {"name": "Tadhg Ó'Súilleabháin", "income": 6900, "scenario": "perfect"},
    {"name": "Orlaith Ní Cheallaigh", "income": 7100, "scenario": "perfect"},
    {"name": "Siobhán O'Connor", "income": 9500, "scenario": "high_flyer"},
    {"name": "Eoin Murphy", "income": 4000, "scenario": "auto_reject"},
    {"name": "Brendan Gleeson", "income": 12000, "scenario": "shady_income"},
    {"name": "Saoirse Ronan", "income": 8500, "scenario": "perfect"},
    {"name": "Paul Mescal", "income": 7300, "scenario": "short_tenure"},
    {"name": "Barry Keoghan", "income": 6900, "scenario": "bad_landlord_ref"},
    {"name": "Andrew Scott", "income": 7700, "scenario": "vague_employer_ref"},
    {"name": "Cillian Murphy", "income": 15000, "scenario": "perfect"},
    {"name": "Ruth Negga", "income": 8200, "scenario": "perfect"},
    {"name": "Domhnall Gleeson", "income": 7400, "scenario": "income_discrepancy"},
    {"name": "Kerry Condon", "income": 6800, "scenario": "missing_id"},
    {"name": "Fiona Shaw", "income": 9000, "scenario": "perfect"},
    {"name": "Colm Meaney", "income": 5800, "scenario": "low_income"},
    {"name": "Jamie Dornan", "income": 8800, "scenario": "perfect"},
    {"name": "Caitriona Balfe", "income": 8300, "scenario": "perfect"},
]

def write_csv(path, data):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["field", "value"])
        for k, v in data.items():
            writer.writerow([k, v])

def generate_applicant(app, index, prop_ids):
    ref_num = f"{index+1:03}"
    ref_dir = DATA_DIR / f"REF-2026-{ref_num}"
    if app['scenario'] == 'missing_docs':
        ref_dir = DATA_DIR / f"REF-2026-{ref_num}_incomplete"
    
    ref_dir.mkdir(parents=True, exist_ok=True)
    
    # Randomly assign a property
    assigned_prop_id = random.choice(prop_ids)
    
    # application_form.csv
    form_data = {
        "ref_number": f"REF-2026-{ref_num}",
        "full_name": app['name'],
        "date_of_birth": "1990-01-01",
        "email": f"{app['name'].lower().replace(' ', '.')}@example.com",
        "phone": "+353 87 000 0000",
        "property_id": assigned_prop_id,
        "employer_name": "Global Solutions Ltd" if app['scenario'] != 'self_employed' else "Self-Employed",
        "employment_type": "Permanent" if app['scenario'] != 'self_employed' else "Contractor",
        "monthly_gross_income": app['income'],
        "reason_for_moving": "Relocation" if app['scenario'] != 'timeline_inconsistency' else "End of lease",
        "num_occupants": 1,
        "consent_gdpr": "Yes",
        "consent_date": "2026-04-10"
    }
    write_csv(ref_dir / "application_form.csv", form_data)
    
    # proof_of_income.csv
    payslip_income = app['income']
    if app['scenario'] == 'income_discrepancy':
        payslip_income -= 1200
    elif app['scenario'] == 'shady_income':
        payslip_income = 25000 # Massive jump from declared
        
    income_data = {
        "gross_monthly_income": payslip_income,
        "employer_name": "Global Solutions Ltd",
        "verified_by_employer": "Yes"
    }
    write_csv(ref_dir / "proof_of_income.csv", income_data)
    
    # cover_letter.txt
    letters = {
        "perfect": f"Dear Siobhán, I am highly interested in Charleston Road. I have lived in Ranelagh for 4 years and love the community. My job at Global Solutions is stable, and I am a quiet, non-smoking professional.",
        "vague_cover": "I need a place to live. I have the money. Call me.",
        "self_employed": "As a self-employed consultant, I have a very stable client base and can provide 3 years of audited accounts. I value a quiet home environment.",
        "high_flyer": "I am a senior executive looking for a premium long-term residence. I can pay the full year upfront if preferred.",
        "auto_reject": "Hi, I don't earn much but I'm very clean.",
        "short_tenure": "I just moved to Ireland and need a place ASAP."
    }
    content = letters.get(app['scenario'], f"Hello, I am {app['name']}. I would like to rent your property. I am a good tenant.")
    with open(ref_dir / "cover_letter.txt", "w", encoding="utf-8") as f:
        f.write(content)
    
    # employer_reference.txt
    emp_refs = {
        "perfect": f"{app['name']} is an exemplary employee. They are reliable, professional, and their position is permanent with high growth potential.",
        "ref_red_flags": f"{app['name']} is currently on a performance improvement plan. Their contract is subject to review next month.",
        "high_income_bad_ref": f"{app['name']} earns a high salary but has had several disciplinary issues regarding workplace conduct.",
        "vague_employer_ref": f"We confirm {app['name']} works here. We do not provide detailed references."
    }
    e_content = emp_refs.get(app['scenario'], f"I confirm {app['name']} is employed here and earns €{app['income']*12} annually.")
    with open(ref_dir / "employer_reference.txt", "w", encoding="utf-8") as f:
        f.write(e_content)
    
    # landlord_reference.txt
    if app['scenario'] != 'missing_docs':
        lan_refs = {
            "perfect": f"{app['name']} was a fantastic tenant for 3 years. Always paid early, kept the garden immaculate, and was very respectful of neighbors.",
            "bad_landlord_ref": f"{app['name']} paid rent but we had several noise complaints from neighbors. The property required professional cleaning after they left.",
            "timeline_inconsistency": f"{app['name']} lived here from 2018 to 2020." # Contradicts 2022-2024
        }
        l_content = lan_refs.get(app['scenario'], f"{app['name']} was a tenant here and paid rent on time.")
        with open(ref_dir / "landlord_reference.txt", "w", encoding="utf-8") as f:
            f.write(l_content)
    
    # photo_id_present.txt
    if app['scenario'] != 'missing_id':
        with open(ref_dir / "photo_id_present.txt", "w", encoding="utf-8") as f:
            f.write("Photo ID submitted: Yes")

# Clear old data
import shutil
if DATA_DIR.exists():
    shutil.rmtree(DATA_DIR)
DATA_DIR.mkdir()

# Load available properties
properties_path = Path("data/properties.csv")
prop_ids = ["PROP-001"] # Fallback
if properties_path.exists():
    with open(properties_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        prop_ids = [row["property_id"] for row in reader]

for i, app in enumerate(applicant_base):
    generate_applicant(app, i, prop_ids)

print(f"Generated {len(applicant_base)} diverse applications across {len(prop_ids)} properties.")
