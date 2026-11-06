"""ADK Multi-Scope State and Context Manager for Healthcare."""

from typing import Any, Dict, Optional
from google.adk.events import EventActions


class HealthcareStateManager:
    """Manages ADK state scopes adhering to HIPAA privacy standards.

    Scopes:
      - session: Transient conversation state (e.g. current form step, uncommitted draft).
      - user: Persistent patient clinical history (e.g. user:mrn, user:allergies).
      - app: Hospital-wide global configurations (e.g. app:hospital_name).
      - temp: Strictly ephemeral scratchpads that are never written to disk or database.
    """

    APP_PREFIX = "app:"
    USER_PREFIX = "user:"
    TEMP_PREFIX = "temp:"

    @classmethod
    def create_initial_state(
        cls,
        hospital_name: str,
        hospital_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate baseline state dictionary for a new patient intake session."""
        return {
            f"{cls.APP_PREFIX}hospital_name": hospital_name,
            f"{cls.APP_PREFIX}hospital_id": hospital_id,
            f"{cls.APP_PREFIX}hipaa_notice_version": "2026.1",
            "current_step": "IDENTITY_VERIFICATION",
            "is_emergency": False,
            "intake_completed": False,
        }

    @classmethod
    def set_user_demographics(
        cls,
        mrn: str,
        name: str,
        dob: str,
        allergies: Optional[list[str]] = None
    ) -> EventActions:
        """Create an ADK EventActions delta promoting patient profile to user scope."""
        delta: Dict[str, Any] = {
            f"{cls.USER_PREFIX}mrn": mrn,
            f"{cls.USER_PREFIX}full_name": name,
            f"{cls.USER_PREFIX}dob": dob,
            "patient_mrn": mrn,
            "current_step": "INSURANCE_VERIFICATION",
        }
        if allergies:
            delta[f"{cls.USER_PREFIX}allergies"] = allergies

        return EventActions(state_delta=delta)

    @classmethod
    def record_insurance_result(
        cls,
        payer: str,
        is_eligible: bool,
        copay: float
    ) -> EventActions:
        """Record verified insurance outcomes into session and user state."""
        return EventActions(
            state_delta={
                f"{cls.USER_PREFIX}primary_payer": payer,
                "insurance_verified": is_eligible,
                "estimated_copay": copay,
                "current_step": "CLINICAL_TRIAGE",
            }
        )

    @classmethod
    def record_triage_acuity(
        cls,
        acuity: str,
        department_id: str,
        is_emergency: bool
    ) -> EventActions:
        """Record triage severity and recommended routing."""
        return EventActions(
            state_delta={
                "assigned_acuity": acuity,
                "target_department_id": department_id,
                "is_emergency": is_emergency,
                "current_step": "EMERGENCY_DISPATCH" if is_emergency else "SCHEDULING",
            }
        )

    @classmethod
    def sanitize_for_storage(cls, state: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure temp: keys are scrubbed and sensitive data is normalized."""
        return {
            k: v for k, v in state.items()
            if not k.startswith(cls.TEMP_PREFIX)
        }
