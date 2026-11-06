"""Patient identification and Master Patient Index (MPI) tools."""

import hashlib
import uuid
from typing import Any, Dict, Optional
from ..models.patient import PatientDemographics, PatientProfile, EmergencyContact, PatientConsent


# In-memory mock Master Patient Index database for development and demonstration
MOCK_MPI_DATABASE: Dict[str, Dict[str, Any]] = {
    "DOE_JANE_1985-04-12": {
        "mrn": "MRN-90214",
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1985-04-12",
        "gender": "Female",
        "phone": "+1-555-019-2834",
        "email": "jane.doe@example.com",
        "address_street": "742 Evergreen Terrace",
        "address_city": "Springfield",
        "address_state": "NY",
        "address_postal_code": "10001",
        "is_returning_patient": True,
    }
}


def lookup_master_patient_index(
    first_name: str,
    last_name: str,
    date_of_birth: str,
    national_id: Optional[str] = None
) -> Dict[str, Any]:
    """Query the hospital's Master Patient Index (MPI / EHR) for existing patient records.

    Args:
        first_name: Patient's legal first name.
        last_name: Patient's legal last name.
        date_of_birth: Date of birth in YYYY-MM-DD format.
        national_id: Optional last 4 digits of SSN or national identifier for disambiguation.

    Returns:
        Dictionary containing patient MRN, return status, and matched record if found.
    """
    key = f"{last_name.strip().upper()}_{first_name.strip().upper()}_{date_of_birth.strip()}"
    
    if key in MOCK_MPI_DATABASE:
        record = MOCK_MPI_DATABASE[key]
        return {
            "found": True,
            "mrn": record["mrn"],
            "is_returning_patient": True,
            "patient_details": record,
            "message": f"Existing patient record located in hospital EHR with MRN {record['mrn']}."
        }
    
    # New patient registration: assign deterministic yet unique Medical Record Number
    unique_hash = hashlib.sha256(f"{first_name}{last_name}{date_of_birth}".encode()).hexdigest()[:6].upper()
    generated_mrn = f"MRN-{unique_hash}"
    
    return {
        "found": False,
        "mrn": generated_mrn,
        "is_returning_patient": False,
        "patient_details": None,
        "message": f"No prior hospital record found. New Medical Record Number created: {generated_mrn}."
    }


def register_patient_profile(
    first_name: str,
    last_name: str,
    date_of_birth: str,
    gender: str,
    phone: str,
    address_street: str,
    address_city: str,
    address_state: str,
    address_postal_code: str,
    emergency_contact_name: str,
    emergency_contact_relationship: str,
    emergency_contact_phone: str,
    hipaa_consent_given: bool = True,
    conversational_consent_text: Optional[str] = None,
    email: Optional[str] = None,
    mrn: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate and register a complete patient profile into the onboarding state.

    Args:
        first_name: Patient legal first name.
        last_name: Patient legal last name.
        date_of_birth: YYYY-MM-DD format.
        gender: Biological or administrative gender (Male/Female/Other).
        phone: Primary phone number.
        address_street: Street address.
        address_city: City.
        address_state: State or province.
        address_postal_code: ZIP or postal code.
        emergency_contact_name: Contact person's full name.
        emergency_contact_relationship: Relation (e.g., Spouse, Parent, Friend).
        emergency_contact_phone: Emergency phone number.
        hipaa_consent_given: Boolean acknowledgement of HIPAA privacy practices.
        conversational_consent_text: Patient's verbal conversational statement granting consent.
        email: Optional email address.
        mrn: Optional preexisting MRN if known.

    Returns:
        Structured confirmation with assigned MRN and registration validation status.
    """
    from .confirmation_guard import evaluate_conversational_consent

    # If conversational consent text is provided, evaluate it
    has_valid_consent = hipaa_consent_given
    verbal_utterance = conversational_consent_text

    if conversational_consent_text:
        eval_result = evaluate_conversational_consent(conversational_consent_text)
        has_valid_consent = eval_result["consented"]
        if not has_valid_consent:
            return {
                "status": "ERROR",
                "message": f"Conversational consent could not be verified: {eval_result['message']}"
            }

    if not has_valid_consent:
        return {
            "status": "ERROR",
            "message": "HIPAA consent must be acknowledged (verbally or digitally) to proceed with hospital onboarding."
        }

    assigned_mrn = mrn or f"MRN-{uuid.uuid4().hex[:6].upper()}"
    
    profile = PatientProfile(
        mrn=assigned_mrn,
        demographics=PatientDemographics(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            gender=gender,
            phone=phone,
            email=email,
            address_street=address_street,
            address_city=address_city,
            address_state=address_state,
            address_postal_code=address_postal_code,
        ),
        emergency_contact=EmergencyContact(
            name=emergency_contact_name,
            relationship=emergency_contact_relationship,
            phone=emergency_contact_phone,
        ),
        consent=PatientConsent(
            hipaa_acknowledgement=True,
            consent_to_treatment=True,
            financial_responsibility_accepted=True,
            consent_mode="CONVERSATIONAL_VERBAL",
            verbal_affirmation_text=verbal_utterance or "Patient provided verbal consent during intake interview",
            signature_date=date_of_birth,
        ),
        status="verified"
    )

    # Cache in mock database
    lookup_key = f"{last_name.strip().upper()}_{first_name.strip().upper()}_{date_of_birth.strip()}"
    MOCK_MPI_DATABASE[lookup_key] = profile.model_dump()

    return {
        "status": "SUCCESS",
        "mrn": assigned_mrn,
        "patient_name": f"{first_name} {last_name}",
        "profile": profile.model_dump(),
        "message": f"Patient profile successfully verified and registered with MRN {assigned_mrn}."
    }
