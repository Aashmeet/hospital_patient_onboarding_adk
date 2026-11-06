"""Master Hospital Onboarding Coordinator Agent supervising specialist subagents."""

from google.adk import Agent
from .intake_agent import create_intake_agent
from .insurance_agent import create_insurance_agent
from .triage_agent import create_triage_agent
from .scheduling_agent import create_scheduling_agent
from ..tools.fhir_tools import export_onboarding_to_fhir_bundle
from ...config.settings import settings

COORDINATOR_INSTRUCTIONS = """\
You are the Chief Patient Experience Coordinator for St. Jude Memorial Health System.
You oversee the end-to-end patient onboarding journey by delegating to specialized clinical and administrative subagents:
1. Delegate to `patient_identity_agent` to verify demographics, assign an MRN, and obtain HIPAA consent.
2. Delegate to `insurance_financial_agent` to verify real-time insurance eligibility and calculate copays.
3. Delegate to `clinical_triage_agent` to evaluate symptoms, score ESI clinical acuity, and screen for medication allergies.
4. Delegate to `scheduling_logistics_agent` to confirm arrival slot, assign attending physician, and issue pre-visit instructions.
5. Finally, call `export_onboarding_to_fhir_bundle` to generate the official HL7 FHIR R4 Bundle for electronic hospital EHR sync.

Maintain an empathetic, reassuring, and highly professional bedside manner at all times.
"""

def create_coordinator_agent() -> Agent:
    """Factory creating the root coordinator agent with full subagent delegation."""
    intake_agent = create_intake_agent()
    insurance_agent = create_insurance_agent()
    triage_agent = create_triage_agent()
    scheduling_agent = create_scheduling_agent()

    return Agent(
        name="onboarding_coordinator_agent",
        model=settings.onboarding_model_name,
        instruction=COORDINATOR_INSTRUCTIONS,
        sub_agents=[intake_agent, insurance_agent, triage_agent, scheduling_agent],
        tools=[export_onboarding_to_fhir_bundle],
    )
