"""Health insurance and eligibility verification domain models."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class EligibilityStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    NOT_FOUND = "NOT_FOUND"


class InsurancePolicy(BaseModel):
    """Patient-submitted insurance details."""
    payer_name: str = Field(..., description="Insurance company name, e.g. Blue Cross Blue Shield, Aetna, UnitedHealthcare")
    payer_id: Optional[str] = Field(None, description="Electronic Payer ID (NAIC / EDI)")
    policy_id: str = Field(..., description="Member / Policy ID number")
    group_number: Optional[str] = Field(None, description="Group plan number")
    subscriber_name: str = Field(..., description="Primary policy holder legal name")
    relationship_to_subscriber: str = Field(default="Self", description="Self, Spouse, Child, Other")


class CoverageDetails(BaseModel):
    """Real-time benefits and eligibility breakdown."""
    plan_name: str = Field(..., description="Commercial PPO, HMO, Medicare Advantage, etc.")
    in_network: bool = Field(default=True, description="Whether hospital is in-network")
    copay_specialist: float = Field(default=0.0, description="Estimated specialist copay in USD")
    copay_primary_care: float = Field(default=0.0, description="Estimated PCP copay in USD")
    deductible_remaining: float = Field(default=0.0, description="Remaining annual deductible in USD")
    coinsurance_rate: float = Field(default=0.20, description="Patient coinsurance percentage (e.g. 0.20 for 20%)")
    prior_authorization_required: bool = Field(default=False, description="Whether procedures require prior auth")


class InsuranceVerificationResult(BaseModel):
    """Verification outcome returned to the patient agent."""
    is_eligible: bool = Field(..., description="Whether coverage is active and verified")
    status: EligibilityStatus = Field(..., description="EDI 271 eligibility status")
    policy: InsurancePolicy
    coverage: Optional[CoverageDetails] = None
    verification_reference_code: str = Field(..., description="EDI 271 transaction reference code")
    estimated_patient_responsibility: float = Field(default=0.0, description="Estimated patient out-of-pocket for visit")
    notes: str = Field(default="", description="Payer notices or restrictions")
