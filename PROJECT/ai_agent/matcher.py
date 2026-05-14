"""
AI Agent Module: Cross-Property Matcher
Identifies "Best Fit" properties for applicants based on rent and beds.
"""

from rpa.property_manager import load_properties

def find_best_fit_properties(app: dict, composite_score: float) -> list[dict]:
    """
    Suggests alternative properties for high-scoring applicants.
    Criteria:
    1. Score must be > 65.
    2. Income must meet the 2.75x rent coverage for the alternative property.
    3. Property must align with applicant preferences (Area, Beds).
    """
    if composite_score < 65:
        return []

    all_props = load_properties()
    suggestions = []
    
    # Extract applicant monthly income
    authoritative_income = app.get("authoritative_income", 0)
    prefs = app.get("preferences", {"area": "Dublin", "beds": 1})
    
    if authoritative_income == 0:
        return []

    for prop in all_props:
        if prop["property_id"] == app["property_id"]:
            continue
            
        rent = float(prop["rent"])
        beds = int(prop["beds"])
        addr = prop["address"]
        
        # Check financial suitability
        if authoritative_income < (rent * 2.75):
            continue
            
        # Check preference alignment
        area_match = prefs["area"].lower() in addr.lower()
        bed_match = beds >= prefs["beds"]
        
        if area_match or bed_match:
            match_reasons = []
            if area_match: match_reasons.append(f"Located in preferred area ({prefs['area']})")
            if bed_match: match_reasons.append(f"Meets/exceeds bed requirement ({prefs['beds']}+)")
            match_reasons.append(f"Income coverage is {authoritative_income/rent:.2f}x")
            
            suggestions.append({
                "property_id": prop["property_id"],
                "address": addr,
                "reason": ". ".join(match_reasons) + f". (Base Score: {composite_score})"
            })
            
    return suggestions
