"""Unit tests for hospital onboarding tools."""

import pytest
from src.tools.identity_tools import lookup_master_patient_index, register_patient_profile
from src.tools.insurance_tools import calculate_patient_cost_estimate, verify_insurance_eligibility
from src.tools.clinical_tools import check_drug_allergy_contraindications, evaluate_clinical_acuity
from src.tools.scheduling_tools import book_appointment_slot, get_available_department_slots
from src.tools.fhir_tools import export_onboarding_to_fhir_bundle


def test_lookup_master_patient_index():
    # Test new patient lookup
    result = lookup_master_patient_index("John", "Smith", "1990-01-01")
    assert result["found"] is False
    assert result["mrn"].startswith("MRN-")

    # Test returning patient lookup
    ret_result = lookup_master_patient_index("Jane", "Doe", "1985-04-12")
    assert ret_result["found"] is True
    assert ret_result["mrn"] == "MRN-90214"


def test_register_patient_profile_requires_consent():
    # Fails when neither explicit nor verbal consent is given
    res = register_patient_profile(
        first_name="Test",
        last_name="Patient",
        date_of_birth="1995-05-05",
        gender="Male",
        phone="+1-555-0100",
        address_street="1 Main St",
        address_city="Albany",
        address_state="NY",
        address_postal_code="12201",
        emergency_contact_name="Contact",
        emergency_contact_relationship="Friend",
        emergency_contact_phone="+1-555-0101",
        hipaa_consent_given=False,
    )
    assert res["status"] == "ERROR"
    assert "HIPAA" in res["message"]

    # Succeeds with standard conversational verbal consent
    verbal_res = register_patient_profile(
        first_name="Test",
        last_name="Patient",
        date_of_birth="1995-05-05",
        gender="Male",
        phone="+1-555-0100",
        address_street="1 Main St",
        address_city="Albany",
        address_state="NY",
        address_postal_code="12201",
        emergency_contact_name="Contact",
        emergency_contact_relationship="Friend",
        emergency_contact_phone="+1-555-0101",
        hipaa_consent_given=False,
        conversational_consent_text="Yes, I agree to the privacy notice and give consent.",
    )
    assert verbal_res["status"] == "SUCCESS"
    assert verbal_res["profile"]["consent"]["consent_mode"] == "CONVERSATIONAL_VERBAL"


def test_insurance_verification():
    # Valid active policy
    res = verify_insurance_eligibility(
        payer_name="Blue Cross Blue Shield",
        policy_id="POL-12345",
        subscriber_name="Jane Doe"
    )
    assert res["is_eligible"] is True
    assert res["status"] == "ACTIVE"
    assert res["coverage"]["in_network"] is True
    assert res["estimated_patient_responsibility"] > 0

    # Lapsed / expired policy
    exp_res = verify_insurance_eligibility(
        payer_name="Aetna",
        policy_id="POL-EXPIRED-999",
        subscriber_name="Jane Doe"
    )
    assert exp_res["is_eligible"] is False
    assert exp_res["status"] == "INACTIVE"


def test_clinical_acuity_emergency_detection():
    # Emergency chest pain
    res = evaluate_clinical_acuity(
        chief_complaint="Severe crushing chest pain and breathlessness",
        symptom_duration="15 mins",
        pain_score=9,
        chronic_conditions=["CAD"],
        current_medications=[],
        patient_allergies=[]
    )
    assert res["is_emergency"] is True
    assert "ESI-2" in res["assigned_acuity"] or "ESI-1" in res["assigned_acuity"]
    assert res["recommended_department_id"] == "dept_urgent_care"

    # Routine joint pain
    routine_res = evaluate_clinical_acuity(
        chief_complaint="Knee stiffness after marathon",
        symptom_duration="5 days",
        pain_score=4,
        chronic_conditions=[],
        current_medications=[],
        patient_allergies=[]
    )
    assert routine_res["is_emergency"] is False
    assert routine_res["recommended_department_id"] == "dept_orthopedics"


def test_drug_allergy_contraindication_check():
    # Conflicting pair: Penicillin allergy with Amoxicillin
    conflict_res = check_drug_allergy_contraindications(
        medications=["Amoxicillin 500mg"],
        allergies=["Penicillin"]
    )
    assert conflict_res["has_conflicts"] is True
    assert conflict_res["conflict_count"] == 1
    assert "Cross-reactivity" in conflict_res["conflicts"][0]["warning"]

    # Safe pair
    safe_res = check_drug_allergy_contraindications(
        medications=["Lisinopril 10mg"],
        allergies=["Sulfa"]
    )
    assert safe_res["has_conflicts"] is False


def test_scheduling_tools():
    slots = get_available_department_slots("dept_cardiology")
    assert slots["found"] is True
    assert len(slots["available_slots"]) > 0

    booking = book_appointment_slot(
        mrn="MRN-TEST-1",
        department_id="dept_cardiology",
        selected_time_slot=slots["available_slots"][0]
    )
    assert booking["status"] == "SUCCESS"
    assert booking["booking_id"].startswith("APP-")


def test_fhir_bundle_export():
    bundle_res = export_onboarding_to_fhir_bundle(
        patient_profile={"mrn": "MRN-101", "demographics": {"first_name": "Alice", "last_name": "Smith"}},
        insurance_data={"is_eligible": True, "policy": {"payer_name": "Cigna", "policy_id": "CIG-900"}},
        clinical_data={"chief_complaint": "Migraine"},
        appointment_data={"department_name": "Neurology", "appointment_time": "2026-11-03 10:00"}
    )
    assert bundle_res["status"] == "SUCCESS"
    bundle = bundle_res["fhir_bundle"]
    assert bundle["resourceType"] == "Bundle"
    assert len(bundle["entry"]) == 3
    resource_types = [e["resource"]["resourceType"] for e in bundle["entry"]]
    assert "Patient" in resource_types
    assert "Coverage" in resource_types
    assert "Encounter" in resource_types
