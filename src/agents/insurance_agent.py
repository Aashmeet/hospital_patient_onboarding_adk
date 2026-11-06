"""Health Insurance and Benefits Verification Agent."""

from google.adk import Agent
from ..models.insurance import InsuranceVerificationResult
from ..tools.insurance_tools import (
    calculate_patient_cost_estimate,
    verify_insurance_eligibility,
)
from ...config.settings import settings

INSURANCE_AGENT_INSTRUCTIONS = """\
You are the Insurance & Financial Services Counselor Agent for St. Jude Memorial Health System.
Your responsibility is to ensure the patient's healthcare coverage is active and verified:
1. Inquire about the patient's primary health insurance carrier, member/policy ID, and subscriber details.
2. Call `verify_insurance_eligibility` to run real-time EDI 270/271 benefit verification.
3. Clearly explain the estimated copay and deductible status to the patient.
4. If the patient is uninsured or self-pay, call `calculate_patient_cost_estimate` to deliver a Good Faith Estimate compliant with the No Surprises Act.
5. If coverage is inactive or denied, offer financial assistance or self-pay sliding fee scale options.
"""

def create_insurance_agent() -> Agent:
    """Factory creating configured ADK Insurance Verification Agent."""
    return Agent(
        name="insurance_financial_agent",
        model=settings.onboarding_model_name,
        instruction=INSURANCE_AGENT_INSTRUCTIONS,
        tools=[verify_insurance_eligibility, calculate_patient_cost_estimate],
        output_schema=InsuranceVerificationResult,
    )
