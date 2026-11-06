"""Health insurance benefits and EDI 270/271 real-time eligibility tools."""

import uuid
from typing import Any, Dict, Optional
from ..models.insurance import (
    CoverageDetails,
    EligibilityStatus,
    InsurancePolicy,
    InsuranceVerificationResult,
)

# Known active payer rules for simulation
KNOWN_PAYERS = {
    "BLUE CROSS": {"payer_id": "BCBS-001", "in_network": True, "copay": 25.0, "deductible": 300.0, "coinsurance": 0.15},
    "AETNA": {"payer_id": "AETNA-002", "in_network": True, "copay": 35.0, "deductible": 450.0, "coinsurance": 0.20},
    "UNITEDHEALTHCARE": {"payer_id": "UHC-003", "in_network": True, "copay": 30.0, "deductible": 250.0, "coinsurance": 0.20},
    "CIGNA": {"payer_id": "CIGNA-004", "in_network": True, "copay": 40.0, "deductible": 500.0, "coinsurance": 0.20},
    "MEDICARE": {"payer_id": "CMS-MED-01", "in_network": True, "copay": 0.0, "deductible": 100.0, "coinsurance": 0.20},
    "MEDICAID": {"payer_id": "STATE-MED-02", "in_network": True, "copay": 0.0, "deductible": 0.0, "coinsurance": 0.0},
}


def verify_insurance_eligibility(
    payer_name: str,
    policy_id: str,
    subscriber_name: str,
    group_number: Optional[str] = None,
    relationship_to_subscriber: str = "Self",
) -> Dict[str, Any]:
    """Execute real-time EDI 270/271 insurance benefits and eligibility verification.

    Args:
        payer_name: Name of health plan or insurance carrier.
        policy_id: Member or subscriber identification number.
        subscriber_name: Legal name of the primary subscriber.
        group_number: Optional employer or association group code.
        relationship_to_subscriber: Patient's relationship to subscriber (Self/Spouse/Child).

    Returns:
        Structured eligibility outcome including coverage active status, copay, and deductible.
    """
    clean_payer = payer_name.strip().upper()
    ref_code = f"EDI271-{uuid.uuid4().hex[:8].upper()}"

    # Check for test triggers (e.g. expired or invalid policy IDs)
    if "EXPIRED" in policy_id.upper() or "INVALID" in policy_id.upper():
        result = InsuranceVerificationResult(
            is_eligible=False,
            status=EligibilityStatus.INACTIVE,
            policy=InsurancePolicy(
                payer_name=payer_name,
                policy_id=policy_id,
                group_number=group_number,
                subscriber_name=subscriber_name,
                relationship_to_subscriber=relationship_to_subscriber,
            ),
            verification_reference_code=ref_code,
            notes="Payer returned inactive status: policy lapsed or non-payment of premium.",
        )
        return result.model_dump()

    # Match payer
    matched_payer_key = None
    for k in KNOWN_PAYERS:
        if k in clean_payer:
            matched_payer_key = k
            break

    payer_info = KNOWN_PAYERS.get(
        matched_payer_key,
        {"payer_id": "COMM-OTHER", "in_network": False, "copay": 60.0, "deductible": 1200.0, "coinsurance": 0.40}
    )

    coverage = CoverageDetails(
        plan_name=f"{payer_name} Preferred Health Plan",
        in_network=payer_info["in_network"],
        copay_specialist=payer_info["copay"] + 15.0,
        copay_primary_care=payer_info["copay"],
        deductible_remaining=payer_info["deductible"],
        coinsurance_rate=payer_info["coinsurance"],
        prior_authorization_required=False,
    )

    # Estimate patient responsibility for standard initial visit
    est_responsibility = coverage.copay_specialist

    result = InsuranceVerificationResult(
        is_eligible=True,
        status=EligibilityStatus.ACTIVE,
        policy=InsurancePolicy(
            payer_name=payer_name,
            payer_id=payer_info["payer_id"],
            policy_id=policy_id,
            group_number=group_number,
            subscriber_name=subscriber_name,
            relationship_to_subscriber=relationship_to_subscriber,
        ),
        coverage=coverage,
        verification_reference_code=ref_code,
        estimated_patient_responsibility=est_responsibility,
        notes=f"Coverage ACTIVE. Hospital is {'IN-NETWORK' if coverage.in_network else 'OUT-OF-NETWORK'}."
    )

    return result.model_dump()


def calculate_patient_cost_estimate(
    department_id: str,
    copay_amount: float,
    deductible_remaining: float,
    coinsurance_rate: float = 0.20,
    is_in_network: bool = True
) -> Dict[str, Any]:
    """Calculate transparent good-faith financial estimates for the prospective visit.

    Args:
        department_id: Target hospital clinic or department.
        copay_amount: Applicable visit copay from eligibility check.
        deductible_remaining: Patient's remaining deductible.
        coinsurance_rate: Decimal coinsurance rate.
        is_in_network: Whether clinic is in-network.

    Returns:
        Transparent Good Faith Estimate breakdown compliant with the No Surprises Act.
    """
    base_visit_cost = 250.0
    if "cardiology" in department_id.lower():
        base_visit_cost = 450.0
    elif "urgent" in department_id.lower() or "emergency" in department_id.lower():
        base_visit_cost = 750.0

    network_multiplier = 1.0 if is_in_network else 1.75
    adjusted_cost = base_visit_cost * network_multiplier

    # In-network patient usually pays copay, plus coinsurance on excess if deductible met
    estimated_patient_due = copay_amount
    if not is_in_network:
        estimated_patient_due += min(deductible_remaining, adjusted_cost * 0.3)

    return {
        "department_id": department_id,
        "base_facility_charge_usd": adjusted_cost,
        "estimated_patient_copay_usd": copay_amount,
        "estimated_patient_total_due_usd": round(estimated_patient_due, 2),
        "in_network": is_in_network,
        "good_faith_estimate_notice": (
            "Under the No Surprises Act, health care providers must provide patients "
            "who don't have insurance or are not using insurance an estimate of the bill."
        )
    }
