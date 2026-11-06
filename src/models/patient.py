"""Patient identity, demographic, and consent domain models."""

from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class EmergencyContact(BaseModel):
    """Emergency contact information for a patient."""
    name: str = Field(..., description="Full legal name of the emergency contact")
    relationship: str = Field(..., description="Relationship to patient, e.g. Spouse, Parent, Sibling")
    phone: str = Field(..., description="Contact telephone number in E.164 or national format")


class PatientConsent(BaseModel):
    """HIPAA and treatment consent agreement via standard conversational consent."""
    hipaa_acknowledgement: bool = Field(
        default=False,
        description="Patient has read and accepted the Notice of Privacy Practices"
    )
    consent_to_treatment: bool = Field(
        default=False,
        description="Consent for hospital staff to administer examination and treatment"
    )
    financial_responsibility_accepted: bool = Field(
        default=False,
        description="Patient accepts financial responsibility for uncovered portions"
    )
    consent_mode: str = Field(
        default="CONVERSATIONAL_VERBAL",
        description="Method of consent: CONVERSATIONAL_VERBAL, DIGITAL_SIGNATURE, or PAPER"
    )
    verbal_affirmation_text: Optional[str] = Field(
        default=None,
        description="Exact conversational utterance expressing consent (e.g. 'Yes, I agree and give consent')"
    )
    signature_date: Optional[str] = Field(
        default=None,
        description="ISO-8601 date or timestamp when conversational consent was given"
    )


class PatientDemographics(BaseModel):
    """Core demographic and identification details."""
    first_name: str = Field(..., description="Patient's legal first name")
    last_name: str = Field(..., description="Patient's legal last name")
    date_of_birth: str = Field(..., description="Date of birth in YYYY-MM-DD format")
    gender: str = Field(..., description="Biological sex / administrative gender: Male, Female, Other")
    national_id: Optional[str] = Field(None, description="National identifier or last 4 of SSN for verification")
    phone: str = Field(..., description="Primary contact phone number")
    email: Optional[str] = Field(None, description="Primary email for patient portal delivery")
    address_street: str = Field(..., description="Residential street address")
    address_city: str = Field(..., description="City")
    address_state: str = Field(..., description="State or Province")
    address_postal_code: str = Field(..., description="Postal / ZIP code")


class PatientProfile(BaseModel):
    """Aggregated patient record for onboarding."""
    mrn: Optional[str] = Field(None, description="Assigned Medical Record Number (MPI)")
    demographics: PatientDemographics
    emergency_contact: EmergencyContact
    consent: PatientConsent
    status: str = Field(default="pending", description="Status: pending, verified, rejected, admitted")
