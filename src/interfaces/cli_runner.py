"""Interactive Terminal Interface and ADK Workflow Runner for Patient Onboarding."""

import argparse
import asyncio
import json
import sys
from typing import Any, Dict
from google.adk import Runner
from ..workflow.onboarding_workflow import create_patient_onboarding_workflow
from ..memory.session_service import get_session_service
from ..observability.audit_logger import HIPAAClinicalAuditLogger
from ..observability.metrics import metrics_tracker
from ...config.settings import settings


SAMPLE_STANDARD_PATIENT = {
    "demographics": {
        "first_name": "Eleanor",
        "last_name": "Vance",
        "date_of_birth": "1982-08-14",
        "gender": "Female",
        "phone": "+1-212-555-0199",
        "email": "eleanor.vance@example.com",
        "address_street": "350 5th Ave",
        "address_city": "New York",
        "address_state": "NY",
        "address_postal_code": "10118",
    },
    "emergency_contact": {
        "name": "Thomas Vance",
        "relationship": "Spouse",
        "phone": "+1-212-555-0188",
    },
    "consent": {
        "hipaa_acknowledgement": True,
        "consent_to_treatment": True,
        "financial_responsibility_accepted": True,
        "conversational_affirmation": "Yes, I acknowledge the HIPAA privacy terms and consent to medical examination.",
    },
    "insurance": {
        "payer_name": "Blue Cross Blue Shield",
        "policy_id": "POL-BCBS-883192",
        "group_number": "GRP-CORP-902",
        "subscriber_name": "Eleanor Vance",
    },
    "clinical": {
        "chief_complaint": "Persistent joint swelling and right knee pain after running",
        "symptom_duration": "4 days",
        "pain_score": 6,
        "allergies": ["Penicillin"],
        "medications": ["Multivitamin daily"],
        "chronic_conditions": ["Mild seasonal asthma"],
    },
}

SAMPLE_EMERGENCY_PATIENT = {
    "demographics": {
        "first_name": "Marcus",
        "last_name": "Sterling",
        "date_of_birth": "1965-11-23",
        "gender": "Male",
        "phone": "+1-212-555-0144",
        "email": "marcus.sterling@example.com",
        "address_street": "100 Broadway",
        "address_city": "New York",
        "address_state": "NY",
        "address_postal_code": "10005",
    },
    "emergency_contact": {
        "name": "Claire Sterling",
        "relationship": "Daughter",
        "phone": "+1-212-555-0133",
    },
    "consent": {
        "hipaa_acknowledgement": True,
        "consent_to_treatment": True,
        "financial_responsibility_accepted": True,
        "conversational_affirmation": "Yes, I acknowledge the HIPAA privacy terms and consent to medical examination.",
    },
    "insurance": {
        "payer_name": "Aetna",
        "policy_id": "POL-AETNA-449102",
        "group_number": "GRP-EXEC-55",
        "subscriber_name": "Marcus Sterling",
    },
    "clinical": {
        "chief_complaint": "Sudden crushing chest pain radiating to left shoulder and shortness of breath",
        "symptom_duration": "45 minutes",
        "pain_score": 9,
        "allergies": ["Sulfa"],
        "medications": ["Atorvastatin 20mg", "Lisinopril 10mg"],
        "chronic_conditions": ["Hypertension", "Hyperlipidemia"],
    },
}


async def run_patient_intake(patient_payload: Dict[str, Any], is_interactive: bool = False) -> Dict[str, Any]:
    """Execute the ADK workflow for a patient intake session."""
    print("=" * 80)
    print(f"🏥 {settings.hospital_name} - ADK Digital Patient Onboarding")
    print("=" * 80)

    metrics_tracker.record_start()
    session_service = get_session_service()
    workflow = create_patient_onboarding_workflow()
    runner = Runner(agent=workflow, session_service=session_service)

    user_name = f"{patient_payload['demographics']['first_name']} {patient_payload['demographics']['last_name']}"
    print(f"\n[1/5] Initiating intake for: {user_name}")

    session = await session_service.create_session(
        app_name="hospital_onboarding",
        user_id=f"user_{patient_payload['demographics']['first_name'].lower()}",
        state={"raw_intake_payload": patient_payload},
    )

    HIPAAClinicalAuditLogger.log_event(
        event_type="INTAKE_SESSION_START",
        actor_id="ADK_RUNNER",
        patient_mrn=None,
        action="SESSION_INITIATION",
        details={"user": user_name},
    )

    # Stream workflow events
    print("[2/5] Executing ADK Graph Workflow Nodes...")
    final_output = None
    async for event in runner.run_async(session=session, node_input=patient_payload):
        if event.message:
            print(f"  ➜ {event.message}")
        if event.output:
            final_output = event.output

    if final_output:
        print("\n" + "=" * 80)
        print("✅ ONBOARDING COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"• Consent Method: Standard Conversational Consent (Verbal Verified)")
        print(f"• Assigned MRN: {final_output.get('mrn')}")
        print(f"• Clinical Acuity: {final_output.get('triage_acuity')}")
        booking = final_output.get("booking", {})
        print(f"• Clinic / Bay: {booking.get('department_name')} ({booking.get('location')})")
        print(f"• Provider: {booking.get('assigned_physician')}")
        print(f"• Time Slot: {booking.get('appointment_time')}")
        print(f"• FHIR R4 Bundle ID: {final_output.get('fhir_bundle_id')}")
        print(f"• Local HAPI FHIR: {final_output.get('hapi_fhir_sync_status')} ({settings.fhir_base_url})")
        print("=" * 80)

        metrics_tracker.record_completion(
            department_id=booking.get("department_id", "unknown"),
            acuity=str(final_output.get("triage_acuity", "Unknown")),
        )
    return final_output or {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Hospital Patient Onboarding ADK CLI")
    parser.add_argument(
        "--scenario",
        choices=["standard", "emergency"],
        default="standard",
        help="Run simulated patient scenario (standard outpatient or emergency diversion)",
    )
    args = parser.parse_args()

    payload = SAMPLE_EMERGENCY_PATIENT if args.scenario == "emergency" else SAMPLE_STANDARD_PATIENT
    asyncio.run(run_patient_intake(payload))


if __name__ == "__main__":
    main()
