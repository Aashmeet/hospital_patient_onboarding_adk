"""Real-time operational metrics for patient intake funnel."""

from collections import defaultdict
from typing import Dict


class OnboardingMetricsTracker:
    """Tracks patient onboarding funnel KPIs, drop-offs, and emergency diversions."""

    def __init__(self) -> None:
        self.total_intakes_started = 0
        self.total_intakes_completed = 0
        self.emergency_diversions = 0
        self.insurance_denials = 0
        self.hitl_interventions = 0
        self.intakes_by_department: Dict[str, int] = defaultdict(int)
        self.acuity_distribution: Dict[str, int] = defaultdict(int)

    def record_start(self) -> None:
        self.total_intakes_started += 1

    def record_completion(self, department_id: str, acuity: str) -> None:
        self.total_intakes_completed += 1
        self.intakes_by_department[department_id] += 1
        self.acuity_distribution[acuity] += 1

    def record_emergency_diversion(self) -> None:
        self.emergency_diversions += 1

    def record_insurance_denial(self) -> None:
        self.insurance_denials += 1

    def record_hitl_escalation(self) -> None:
        self.hitl_interventions += 1

    def get_summary(self) -> Dict[str, object]:
        completion_rate = (
            (self.total_intakes_completed / self.total_intakes_started * 100)
            if self.total_intakes_started > 0 else 0.0
        )
        return {
            "intakes_started": self.total_intakes_started,
            "intakes_completed": self.total_intakes_completed,
            "completion_rate_pct": round(completion_rate, 2),
            "emergency_diversions": self.emergency_diversions,
            "insurance_denials": self.insurance_denials,
            "hitl_interventions": self.hitl_interventions,
            "department_breakdown": dict(self.intakes_by_department),
            "acuity_breakdown": dict(self.acuity_distribution),
        }


metrics_tracker = OnboardingMetricsTracker()
