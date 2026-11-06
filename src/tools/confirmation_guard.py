"""Human-in-the-loop (HITL) tool confirmation guardrails and Conversational Consent validation."""

import datetime
import re
from typing import Any, Callable, Dict, Optional

AFFIRMATIVE_CONSENT_PATTERNS = [
    r"\b(yes|yeah|yep|sure|ok|okay|agree|i agree|consent|i consent|accept|i accept|proceed|confirm|confirmed|sounds good|go ahead)\b",
    r"\b(i acknowledge|i understand and agree|i authorize|grant consent)\b"
]

NEGATIVE_CONSENT_PATTERNS = [
    r"\b(no|nope|decline|i decline|disagree|i disagree|do not consent|don\'t consent|refuse|cancel|stop)\b"
]


def evaluate_conversational_consent(utterance: str) -> Dict[str, Any]:
    """Parse patient natural language conversational response to verify legal consent.

    Args:
        utterance: Patient's verbal/textual statement during onboarding dialog.

    Returns:
        Structured consent validation outcome with timestamp and audit trail.
    """
    clean_text = utterance.strip().lower()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Check negative / revocation first
    for neg in NEGATIVE_CONSENT_PATTERNS:
        if re.search(neg, clean_text, re.IGNORECASE):
            return {
                "consented": False,
                "status": "DECLINED",
                "utterance": utterance,
                "timestamp": now_iso,
                "message": "Patient explicitly declined or withheld consent."
            }

    # Check affirmative
    for aff in AFFIRMATIVE_CONSENT_PATTERNS:
        if re.search(aff, clean_text, re.IGNORECASE):
            return {
                "consented": True,
                "status": "ACCEPTED",
                "consent_mode": "CONVERSATIONAL_VERBAL",
                "utterance": utterance,
                "timestamp": now_iso,
                "message": "Valid verbal/conversational consent established under hospital intake policy."
            }

    # Ambiguous or non-committal
    return {
        "consented": False,
        "status": "AMBIGUOUS",
        "utterance": utterance,
        "timestamp": now_iso,
        "message": "Response was ambiguous. Please confirm with 'Yes, I agree' or 'I consent'."
    }


def build_confirmation_guard(
    action_name: str,
    warning_prompt: str
) -> Callable[..., Dict[str, Any]]:
    """Generates an ADK-compliant confirmation predicate for high-consequence tools.

    Args:
        action_name: The tool action being guarded (e.g. 'Commit Financial Responsibility').
        warning_prompt: Disclaimer shown to patient or clinician.

    Returns:
        Callable guardrail function.
    """
    def guard(user_confirmed: bool = False, verbal_response: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        if verbal_response:
            consent_eval = evaluate_conversational_consent(verbal_response)
            if consent_eval["consented"]:
                return {
                    "status": "CONFIRMED",
                    "action": action_name,
                    "consent_eval": consent_eval
                }
            return {
                "requires_confirmation": True,
                "action": action_name,
                "warning": warning_prompt,
                "reason": consent_eval["message"],
                "prompt": "Conversational confirmation required: Please reply with 'Yes, I consent' to proceed."
            }

        if not user_confirmed:
            return {
                "requires_confirmation": True,
                "action": action_name,
                "warning": warning_prompt,
                "prompt": "Please confirm this action with 'YES' or conversational consent to proceed."
            }
        return {"status": "CONFIRMED", "action": action_name}

    return guard
