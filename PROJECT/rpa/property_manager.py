"""
RPA Utility: Property Manager
Handles CRUD operations for the properties dataset.
"""

import csv
from pathlib import Path
from config.settings import PROPERTIES_PATH

def load_properties() -> list[dict]:
    """Loads all properties from the CSV file."""
    if not PROPERTIES_PATH.exists():
        return []
    
    properties = []
    with open(PROPERTIES_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            properties.append(row)
    return properties

def get_property(property_id: str) -> dict:
    """Retrieves a specific property by its ID."""
    props = load_properties()
    for p in props:
        if p["property_id"] == property_id:
            return p
    return {}

def add_property(prop_data: dict) -> bool:
    """Adds a new property to the CSV."""
    file_exists = PROPERTIES_PATH.exists()
    fieldnames = ["property_id", "address", "rent", "beds", "requirements", "landlord_note"]
    
    # Ensure rent and beds are numeric strings
    prop_data["rent"] = str(prop_data.get("rent", 0))
    prop_data["beds"] = str(prop_data.get("beds", 0))
    
    try:
        with open(PROPERTIES_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(prop_data)
        return True
    except Exception as e:
        print(f"Error adding property: {e}")
        return False

def update_property(property_id: str, updated_data: dict) -> bool:
    """Updates an existing property."""
    props = load_properties()
    found = False
    for i, p in enumerate(props):
        if p["property_id"] == property_id:
            props[i].update(updated_data)
            found = True
            break
    
    if not found:
        return False
        
    fieldnames = ["property_id", "address", "rent", "beds", "requirements", "landlord_note"]
    try:
        with open(PROPERTIES_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(props)
        return True
    except Exception as e:
        print(f"Error updating property: {e}")
        return False
