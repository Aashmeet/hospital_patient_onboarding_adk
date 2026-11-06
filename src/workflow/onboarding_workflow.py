"""Deterministic graph-based patient onboarding workflow using ADK."""

from typing import Any, Dict
from google.adk import Event, Workflow
from google.adk.workflow import DEFAULT_ROUTE, START
from .routes import OnboardingRoute
from ..tools.identity_tools import register_patient_profile
from ..tools.insurance_tools import calculate_patient_cost_estimate, verify_insurance_eligibility
from ..tools.clinical_tools import check_drug_allergy_contraindications, evaluate_clinical_acuity
from ..tools.scheduling_tools import book_appointment_slot, get_available_department_slots
from ..tools.fhir_tools import export_onboarding_to_fhir_bundle, sync_fhir_bundle_to_hapi_server
from ...config.settings import settings


def intake_node(node_input: Dict[str, Any]) -> Any:
    """Validate identity, demographics, and standard conversational consent."""
    demographics = node_input.get("demographics", {})
    consent = node_input.get("consent", {})
    emergency_contact = node_input.get("emergency_contact", {})

    conversational_text = consent.get("conversational_affirmation") or consent.get("verbal_affirmation_text")
    explicit_ack = consent.get("hipaa_acknowledgement", False)

    if not explicit_ack and not conversational_text:
        yield Event(
            message="Notice: Conversational consent ('Yes, I agree and grant consent') is required before clinical intake.",
            route=OnboardingRoute.RETRY_IDENTITY.value,
        )
        return

    result = register_patient_profile(
        first_name=demographics.get("first_name", "Valued"),
        last_name=demographics.get("last_name", "Patient"),
        date_of_birth=demographics.get("date_of_birth", "1990-01-01"),
        gender=demographics.get("gender", "Other"),
        phone=demographics.get("phone", "+1-555-0000"),
        address_street=demographics.get("address_street", "1 Hospital Way"),
        address_city=demographics.get("address_city", "New York"),
        address_state=demographics.get("address_state", "NY"),
        address_postal_code=demographics.get("address_postal_code", "10001"),
        emergency_contact_name=emergency_contact.get("name", "Family Member"),
        emergency_contact_relationship=emergency_contact.get("relationship", "Next of Kin"),
        emergency_contact_phone=emergency_contact.get("phone", "+1-555-9999"),
        hipaa_consent_given=explicit_ack,
        conversational_consent_text=conversational_text,
        email=demographics.get("email"),
    )

    if result.get("status") == "ERROR":
        yield Event(
            message=f"Consent Error: {result.get('message')}",
            route=OnboardingRoute.RETRY_IDENTITY.value,
        )
        return

    node_input["patient_profile"] = result
    node_input["mrn"] = result["mrn"]

    yield Event(
        message=f"Patient demographics verified via conversational consent. Assigned Hospital MRN: {result['mrn']}.",
        route=DEFAULT_ROUTE,
    )
    yield node_input


def insurance_node(node_input: Dict[str, Any]) -> Any:
    """Verify health insurance benefits and calculate estimated costs."""
    insurance = node_input.get("insurance", {})
    payer_name = insurance.get("payer_name", "Self-Pay")
    policy_id = insurance.get("policy_id", "SELFPAY-001")
    subscriber = insurance.get("subscriber_name", "Self")

    eligibility = verify_insurance_eligibility(
        payer_name=payer_name,
        policy_id=policy_id,
        subscriber_name=subscriber,
        group_number=insurance.get("group_number"),
    )

    node_input["insurance_verification"] = eligibility

    yield Event(
        message=(
            f"Insurance status: {eligibility['status']} for {payer_name}. "
            f"Estimated visit copay: ${eligibility.get('estimated_patient_responsibility', 0.0):.2f}."
        )
    )
    yield node_input


def triage_node(node_input: Dict[str, Any]) -> Any:
    """Evaluate clinical symptoms, ESI acuity, and check allergy contraindications."""
    clinical = node_input.get("clinical", {})
    chief_complaint = clinical.get("chief_complaint", "General consultation")
    pain_score = int(clinical.get("pain_score", 0))
    symptom_duration = clinical.get("symptom_duration", "1 day")
    allergies = clinical.get("allergies", [])
    medications = clinical.get("medications", [])
    chronic_conditions = clinical.get("chronic_conditions", [])

    # Screen drug-allergy interactions
    drug_check = check_drug_allergy_contraindications(medications, allergies)
    node_input["drug_safety_check"] = drug_check

    # Evaluate Emergency Severity Index (ESI)
    acuity_result = evaluate_clinical_acuity(
        chief_complaint=chief_complaint,
        symptom_duration=symptom_duration,
        pain_score=pain_score,
        chronic_conditions=chronic_conditions,
        current_medications=medications,
        patient_allergies=allergies,
    )
    node_input["triage_result"] = acuity_result

    if acuity_result["is_emergency"]:
        yield Event(
            message=(
                f"CRITICAL CLINICAL ALERT: Emergency symptoms detected: "
                f"{acuity_result['detected_red_flags']}. Diverting immediately to Emergency Triage!"
            ),
            route=OnboardingRoute.EMERGENCY_DISPATCH.value,
        )
        yield node_input
    else:
        yield Event(
            message=(
                f"Triage complete. Assigned Acuity: {acuity_result['assigned_acuity']}. "
                f"Recommended clinic: {acuity_result['recommended_department_id']}."
            ),
            route=DEFAULT_ROUTE,
        )
        yield node_input


def emergency_dispatch_node(node_input: Dict[str, Any]) -> Any:
    """Immediate clinical bypass routing for emergent or resuscitation cases."""
    mrn = node_input.get("mrn", "UNKNOWN")
    triage = node_input.get("triage_result", {})

    booking = book_appointment_slot(
        mrn=mrn,
        department_id="dept_urgent_care",
        selected_time_slot="IMMEDIATE_WALK_IN",
    )
    node_input["appointment_booking"] = booking

    yield Event(
        message=(
            f"EMERGENCY ADMISSION CODE: {booking['booking_id']}. "
            "Patient flagged for immediate clinician bedside evaluation at Ground Floor Emergency Bay 1."
        )
    )
    yield node_input


def scheduling_node(node_input: Dict[str, Any]) -> Any:
    """Book confirmed slot in the recommended outpatient specialty clinic."""
    mrn = node_input.get("mrn", "UNKNOWN")
    triage = node_input.get("triage_result", {})
    recommended_dept = triage.get("recommended_department_id", "dept_internal_med")

    slots_info = get_available_department_slots(recommended_dept)
    available_slots = slots_info.get("available_slots", ["2026-11-02 09:00"])
    chosen_slot = available_slots[0] if available_slots else "2026-11-02 09:00"

    booking = book_appointment_slot(
        mrn=mrn,
        department_id=recommended_dept,
        selected_time_slot=chosen_slot,
    )
    node_input["appointment_booking"] = booking

    yield Event(
        message=(
            f"Consultation scheduled with {booking['assigned_physician']} at "
            f"{booking['department_name']} on {booking['appointment_time']}. Location: {booking['location']}."
        )
    )
    yield node_input


def fhir_sync_node(node_input: Dict[str, Any]) -> Dict[str, Any]:
    """Assemble final HL7 FHIR R4 Transaction Bundle and sync to HAPI FHIR server."""
    bundle_result = export_onboarding_to_fhir_bundle(
        patient_profile=node_input.get("patient_profile", {}),
        insurance_data=node_input.get("insurance_verification", {}),
        clinical_data=node_input.get("clinical", {}),
        appointment_data=node_input.get("appointment_booking", {}),
    )
    
    # Transmit to local mock HAPI FHIR container
    hapi_sync_result = sync_fhir_bundle_to_hapi_server(
        bundle=bundle_result["fhir_bundle"],
        fhir_base_url=settings.fhir_base_url
    )
    bundle_result["hapi_sync"] = hapi_sync_result
    node_input["fhir_sync"] = bundle_result

    final_summary = {
        "status": "COMPLETED",
        "mrn": node_input.get("mrn"),
        "triage_acuity": node_input.get("triage_result", {}).get("assigned_acuity"),
        "booking": node_input.get("appointment_booking"),
        "fhir_bundle_id": bundle_result["bundle_id"],
        "hapi_fhir_sync_status": hapi_sync_result.get("status"),
        "onboarding_summary": (
            f"Patient onboarding successfully completed. MRN: {node_input.get('mrn')}. "
            f"FHIR Bundle: {bundle_result['bundle_id']} synced to HAPI FHIR ({hapi_sync_result.get('status')})."
        )
    }
    return final_summary


def create_patient_onboarding_workflow() -> Workflow:
    """Construct the graph-based patient onboarding execution workflow."""
    return Workflow(
        name="patient_onboarding_workflow",
        edges=[
            (START, intake_node, insurance_node, triage_node),
            (
                triage_node,
                {
                    OnboardingRoute.EMERGENCY_DISPATCH.value: emergency_dispatch_node,
                    DEFAULT_ROUTE: scheduling_node,
                },
            ),
            (emergency_dispatch_node, fhir_sync_node),
            (scheduling_node, fhir_sync_node),
        ],
    )
