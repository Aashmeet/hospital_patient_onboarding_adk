"""Unit tests for Observability, HIPAA sanitization, and metrics."""

import pytest
from src.observability.hipaa_sanitizer import redact_phi_text, sanitize_phi_dict
from src.observability.audit_logger import HIPAAClinicalAuditLogger
from src.observability.metrics import OnboardingMetricsTracker


def test_redact_phi_text():
    raw_text = "Patient SSN is 123-45-6789 and phone is 212-555-0199 with email jane@example.com."
    sanitized = redact_phi_text(raw_text)
    assert "[REDACTED_SSN]" in sanitized
    assert "123-45-6789" not in sanitized
    assert "[REDACTED_PHONE]" in sanitized
    assert "212-555-0199" not in sanitized
    assert "[REDACTED_EMAIL]" in sanitized
    assert "jane@example.com" not in sanitized


def test_sanitize_phi_dict():
    payload = {
        "first_name": "Jane",
        "ssn": "987-65-4321",
        "phone": "+1-555-0123",
        "nested": {
            "email": "test@clinic.org",
            "token": "secret_token_val"
        }
    }
    cleaned = sanitize_phi_dict(payload)
    assert cleaned["ssn"] == "[REDACTED_SECRET]"
    assert "[REDACTED_PHONE]" in cleaned["phone"]
    assert "[REDACTED_EMAIL]" in cleaned["nested"]["email"]
    assert cleaned["nested"]["token"] == "[REDACTED_SECRET]"


def test_hipaa_audit_logger():
    entry = HIPAAClinicalAuditLogger.log_event(
        event_type="DEMOGRAPHICS_UPDATE",
        actor_id="NURSE_01",
        patient_mrn="MRN-998877",
        action="UPDATE_ADDRESS",
        details={"phone": "+1-555-9000", "new_city": "New York"}
    )
    assert entry["audit_standard"] == "HIPAA-Security-Rule-164.312(b)"
    assert entry["patient_mrn"] == "MRN-998877"
    assert "[REDACTED_PHONE]" in entry["details"]["phone"]


def test_metrics_tracker():
    tracker = OnboardingMetricsTracker()
    tracker.record_start()
    tracker.record_completion(department_id="dept_cardiology", acuity="ESI-3")
    tracker.record_emergency_diversion()

    summary = tracker.get_summary()
    assert summary["intakes_started"] == 1
    assert summary["intakes_completed"] == 1
    assert summary["completion_rate_pct"] == 100.0
    assert summary["emergency_diversions"] == 1
    assert summary["department_breakdown"]["dept_cardiology"] == 1
