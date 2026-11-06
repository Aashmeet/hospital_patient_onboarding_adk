"""Routing definitions and branch conditions for the patient onboarding graph."""

from enum import Enum


class OnboardingRoute(str, Enum):
    """Workflow branch routing keys."""
    RETRY_IDENTITY = "retry_identity"
    EMERGENCY_DISPATCH = "emergency_dispatch"
    NORMAL_SCHEDULING = "normal_scheduling"
    INSURANCE_RETRY = "insurance_retry"
    COMPLETED = "completed"
