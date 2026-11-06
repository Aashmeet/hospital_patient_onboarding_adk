"""Test fixtures and mock payloads for Hospital Patient Onboarding."""

import pytest
from typing import Any, Dict


@pytest.fixture
def mock_standard_patient() -> Dict[str, Any]:
    return {
        "demographics": {
            "first_name": "Eleanor",
            "last_name": "Vance",
            "date_of_birth": "1982-08-14",
            "gender": "Female",
            "phone": "+1-212-555-0199",
            "email": "eleanor.vance@example.com",
            "address_street": "350 5th Ave",
            "address_city": "New York",
            "address_state": "NY",
            "address_postal_code": "10118",
        },
        "emergency_contact": {
            "name": "Thomas Vance",
            "relationship": "Spouse",
            "phone": "+1-212-555-0188",
        },
        "consent": {
            "hipaa_acknowledgement": True,
            "consent_to_treatment": True,
            "financial_responsibility_accepted": True,
        },
        "insurance": {
            "payer_name": "Blue Cross Blue Shield",
            "policy_id": "POL-BCBS-883192",
            "group_number": "GRP-CORP-902",
            "subscriber_name": "Eleanor Vance",
        },
        "clinical": {
            "chief_complaint": "Joint swelling and right knee pain after running",
            "symptom_duration": "4 days",
            "pain_score": 6,
            "allergies": ["Penicillin"],
            "medications": ["Multivitamin daily"],
            "chronic_conditions": ["Mild asthma"],
        },
    }


@pytest.fixture
def mock_emergency_patient() -> Dict[str, Any]:
    return {
        "demographics": {
            "first_name": "Marcus",
            "last_name": "Sterling",
            "date_of_birth": "1965-11-23",
            "gender": "Male",
            "phone": "+1-212-555-0144",
            "address_street": "100 Broadway",
            "address_city": "New York",
            "address_state": "NY",
            "address_postal_code": "10005",
        },
        "emergency_contact": {
            "name": "Claire Sterling",
            "relationship": "Daughter",
            "phone": "+1-212-555-0133",
        },
        "consent": {
            "hipaa_acknowledgement": True,
            "consent_to_treatment": True,
            "financial_responsibility_accepted": True,
        },
        "insurance": {
            "payer_name": "Aetna",
            "policy_id": "POL-AETNA-449102",
            "subscriber_name": "Marcus Sterling",
        },
        "clinical": {
            "chief_complaint": "Sudden crushing chest pain radiating to left shoulder and severe shortness of breath",
            "symptom_duration": "30 minutes",
            "pain_score": 9,
            "allergies": [],
            "medications": ["Lisinopril 10mg"],
            "chronic_conditions": ["Hypertension"],
        },
    }
