"""Hospital scheduling and clinical slot reservation tools."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

DEPARTMENTS_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "hospital_departments.json"


def _load_department_data() -> Dict[str, Any]:
    if DEPARTMENTS_CONFIG_PATH.exists():
        with open(DEPARTMENTS_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"departments": []}


def get_available_department_slots(department_id: str) -> Dict[str, Any]:
    """Retrieve open consultation slots and details for a hospital department.

    Args:
        department_id: Target department id (e.g. dept_cardiology, dept_orthopedics, dept_internal_med, dept_urgent_care).

    Returns:
        Department location, physician lead, pre-visit instructions, and open appointment slots.
    """
    data = _load_department_data()
    dept = next((d for d in data.get("departments", []) if d["id"].lower() == department_id.lower()), None)
    
    if not dept:
        return {
            "found": False,
            "error": f"Department '{department_id}' not found in hospital directory."
        }

    return {
        "found": True,
        "department_id": dept["id"],
        "department_name": dept["name"],
        "location": dept["location"],
        "lead_physician": dept["lead_physician"],
        "prep_instructions": dept["prep_instructions"],
        "available_slots": dept["available_slots"]
    }


def book_appointment_slot(
    mrn: str,
    department_id: str,
    selected_time_slot: str
) -> Dict[str, Any]:
    """Confirm and lock a clinical appointment slot for an onboarded patient.

    Args:
        mrn: Patient's assigned Medical Record Number.
        department_id: Target hospital clinical department.
        selected_time_slot: Chosen appointment slot or 'IMMEDIATE_WALK_IN'.

    Returns:
        Structured appointment booking record with confirmation code.
    """
    dept_info = get_available_department_slots(department_id)
    if not dept_info.get("found"):
        return {"status": "FAILED", "error": dept_info.get("error")}

    booking_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
    status = "ESCALATED_EMERGENCY" if selected_time_slot == "IMMEDIATE_WALK_IN" else "CONFIRMED"

    return {
        "status": "SUCCESS",
        "booking_id": booking_id,
        "mrn": mrn,
        "department_id": department_id,
        "department_name": dept_info["department_name"],
        "assigned_physician": dept_info["lead_physician"],
        "appointment_time": selected_time_slot,
        "location": dept_info["location"],
        "prep_instructions": dept_info["prep_instructions"],
        "booking_status": status,
        "confirmation_message": (
            f"Appointment {booking_id} successfully confirmed for patient {mrn} "
            f"at {dept_info['department_name']} on {selected_time_slot}."
        )
    }
