"""HIPAA PHI and PII redaction filter for logging, metrics, and tracing spans."""

import re
from typing import Any, Dict, List, Union

# Common PHI/PII regex patterns
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b")
PHONE_REGEX = re.compile(r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
DOB_REGEX = re.compile(r"\b(19|20)\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b")
POLICY_REGEX = re.compile(r"\b(POL|GRP|MEM|SUB)-[A-Za-z0-9]{4,12}\b", re.IGNORECASE)


def redact_phi_text(text: str) -> str:
    """Mask sensitive healthcare identifiers and PII in raw text."""
    if not isinstance(text, str):
        return str(text)

    sanitized = SSN_REGEX.sub("[REDACTED_SSN]", text)
    sanitized = PHONE_REGEX.sub("[REDACTED_PHONE]", sanitized)
    sanitized = EMAIL_REGEX.sub("[REDACTED_EMAIL]", sanitized)
    sanitized = POLICY_REGEX.sub("[REDACTED_POLICY_ID]", sanitized)
    return sanitized


def sanitize_phi_dict(data: Union[Dict[str, Any], List[Any], Any]) -> Any:
    """Recursively scrub Protected Health Information (PHI) from nested dictionaries."""
    if isinstance(data, dict):
        scrubbed = {}
        for k, v in data.items():
            lower_k = k.lower()
            if any(term in lower_k for term in ["national_id", "ssn", "password", "token", "secret"]):
                scrubbed[k] = "[REDACTED_SECRET]"
            elif any(term in lower_k for term in ["phone", "email", "address"]):
                scrubbed[k] = redact_phi_text(str(v)) if v else v
            else:
                scrubbed[k] = sanitize_phi_dict(v)
        return scrubbed
    elif isinstance(data, list):
        return [sanitize_phi_dict(item) for item in data]
    elif isinstance(data, str):
        return redact_phi_text(data)
    return data
