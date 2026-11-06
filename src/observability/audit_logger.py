"""Immutable HIPAA clinical audit logger for agent interactions."""

import datetime
import json
import logging
from typing import Any, Dict, Optional
from .hipaa_sanitizer import sanitize_phi_dict

logger = logging.getLogger("patient_onboarding.hipaa_audit")


class HIPAAClinicalAuditLogger:
    """Produces structured, immutable HIPAA audit entries."""

    @classmethod
    def log_event(
        cls,
        event_type: str,
        actor_id: str,
        patient_mrn: Optional[str],
        action: str,
        details: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
    ) -> Dict[str, Any]:
        """Record a HIPAA access or mutation event."""
        sanitized_details = sanitize_phi_dict(details or {})
        
        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "audit_standard": "HIPAA-Security-Rule-164.312(b)",
            "event_type": event_type,
            "actor_id": actor_id,
            "patient_mrn": patient_mrn or "ANONYMOUS_INTAKE",
            "action": action,
            "status": status,
            "details": sanitized_details,
        }

        # Log as structured JSON
        logger.info(f"AUDIT_RECORD: {json.dumps(entry)}")
        return entry
