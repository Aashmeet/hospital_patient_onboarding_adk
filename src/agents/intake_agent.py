"""Patient Demographics and Identity Intake Agent."""

from google.adk import Agent
from ..models.patient import PatientProfile
from ..tools.identity_tools import lookup_master_patient_index, register_patient_profile
from ...config.settings import settings

INTAKE_AGENT_INSTRUCTIONS = """\
You are the Patient Identity & Demographics Intake Agent for St. Jude Memorial Health System.
Your job is to onboard new or returning patients by collecting and verifying their identity:
1. Greet the patient warmly and professionally.
2. Collect full legal name, date of birth (YYYY-MM-DD), contact phone, and address.
3. Check the hospital Master Patient Index (MPI) via `lookup_master_patient_index`.
4. Obtain emergency contact details (name, relationship, phone).
5. Ensure the patient acknowledges the HIPAA Notice of Privacy Practices.
6. Register the complete profile using `register_patient_profile`.

Always verify information gently and ensure compliance with healthcare privacy regulations.
"""

def create_intake_agent() -> Agent:
    """Factory creating configured ADK Intake Agent."""
    return Agent(
        name="patient_identity_agent",
        model=settings.onboarding_model_name,
        instruction=INTAKE_AGENT_INSTRUCTIONS,
        tools=[lookup_master_patient_index, register_patient_profile],
        output_schema=PatientProfile,
    )
