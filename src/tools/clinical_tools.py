"""Clinical symptom triage, Emergency Severity Index (ESI), and allergy checking tools."""

import re
from typing import Any, Dict, List
from ..models.clinical import AcuityLevel, Allergy, ClinicalIntake, Medication

# Critical Red Flag patterns requiring immediate emergency department bypass
RED_FLAG_PATTERNS = [
    r"\b(chest pain|pressure in chest|heart attack|angina)\b",
    r"\b(shortness of breath|difficulty breathing|gasping|can\'t breathe)\b",
    r"\b(slurred speech|facial droop|sudden weakness|stroke|numbness on one side)\b",
    r"\b(severe allergic reaction|anaphylaxis|throat swelling|lip swelling)\b",
    r"\b(unconscious|passed out|fainting|unresponsive|syncope)\b",
    r"\b(uncontrolled bleeding|coughing blood|vomiting blood|hemorrhage)\b",
    r"\b(suicidal|self harm|overdose)\b"
]

# Common high-risk drug-allergy contraindication pairs
CONTRAINDICATION_RULES = {
    "PENICILLIN": ["AMOXICILLIN", "AMPICILLIN", "AUGMENTIN", "PIPERACILLIN", "PENICILLIN VK"],
    "SULFA": ["BACTRIM", "SEPTRA", "SULFAMETHOXAZOLE", "SULFASALAZINE"],
    "ASPIRIN": ["IBUPROFEN", "NAPROXEN", "ALEVE", "ADVIL", "MOTRIN", "KETOROLAC"],
    "CODEINE": ["TRAMADOL", "MORPHINE", "OXYCODONE", "HYDROCODONE"],
}


def evaluate_clinical_acuity(
    chief_complaint: str,
    symptom_duration: str,
    pain_score: int,
    chronic_conditions: List[str],
    current_medications: List[str],
    patient_allergies: List[str]
) -> Dict[str, Any]:
    """Execute Emergency Severity Index (ESI) clinical triage on patient symptoms.

    Args:
        chief_complaint: The patient's reported symptoms or reason for visit.
        symptom_duration: How long symptoms have been ongoing.
        pain_score: Numeric pain rating from 0 to 10.
        chronic_conditions: List of known existing conditions (e.g. CAD, COPD, Diabetes).
        current_medications: Current active medications.
        patient_allergies: Known drug or substance allergies.

    Returns:
        Structured clinical evaluation with assigned ESI Acuity, red flag flags, and recommended department.
    """
    detected_red_flags: List[str] = []
    complaint_lower = chief_complaint.lower()

    for pattern in RED_FLAG_PATTERNS:
        match = re.search(pattern, complaint_lower, re.IGNORECASE)
        if match:
            detected_red_flags.append(match.group(0))

    # Triage Decision Tree (ESI 1 through 5)
    if detected_red_flags:
        if any(term in complaint_lower for term in ["unconscious", "unresponsive", "severe allergic reaction", "cardiac"]):
            acuity = AcuityLevel.ESI_1_RESUSCITATION
            dept_id = "dept_urgent_care"
            is_emergency = True
        else:
            acuity = AcuityLevel.ESI_2_EMERGENT
            dept_id = "dept_urgent_care"
            is_emergency = True
    elif pain_score >= 8:
        acuity = AcuityLevel.ESI_3_URGENT
        is_emergency = False
        # Route by organ system
        if any(w in complaint_lower for w in ["bone", "fracture", "joint", "knee", "shoulder", "back", "sprain"]):
            dept_id = "dept_orthopedics"
        elif any(w in complaint_lower for w in ["heart", "palpitation", "blood pressure", "hypertension"]):
            dept_id = "dept_cardiology"
        elif any(w in complaint_lower for w in ["headache", "migraine", "dizziness", "tremor"]):
            dept_id = "dept_neurology"
        else:
            dept_id = "dept_internal_med"
    elif pain_score >= 4 or len(chronic_conditions) > 2:
        acuity = AcuityLevel.ESI_3_URGENT
        is_emergency = False
        if any(w in complaint_lower for w in ["knee", "hip", "ankle", "joint", "wrist", "back"]):
            dept_id = "dept_orthopedics"
        elif any(w in complaint_lower for w in ["heart", "palpitation", "flutter", "edema"]):
            dept_id = "dept_cardiology"
        elif any(w in complaint_lower for w in ["memory", "numbness", "tingling", "nerve"]):
            dept_id = "dept_neurology"
        else:
            dept_id = "dept_internal_med"
    elif pain_score > 0:
        acuity = AcuityLevel.ESI_4_LESS_URGENT
        is_emergency = False
        dept_id = "dept_internal_med"
    else:
        acuity = AcuityLevel.ESI_5_NON_URGENT
        is_emergency = False
        dept_id = "dept_internal_med"

    return {
        "is_emergency": is_emergency,
        "assigned_acuity": acuity.value,
        "recommended_department_id": dept_id,
        "detected_red_flags": detected_red_flags,
        "requires_immediate_clinician_dispatch": is_emergency,
        "triage_summary": (
            f"Triage assigned {acuity.value}. "
            f"Department recommended: {dept_id}. "
            f"Red flags: {', '.join(detected_red_flags) if detected_red_flags else 'None detected'}."
        )
    }


def check_drug_allergy_contraindications(
    medications: List[str],
    allergies: List[str]
) -> Dict[str, Any]:
    """Screen patient's active home medications against documented allergies.

    Args:
        medications: List of current medications (e.g. Amoxicillin, Lisinopril).
        allergies: List of patient allergens (e.g. Penicillin, Sulfa).

    Returns:
        Structured safety screening with identified contraindications and severity.
    """
    conflicts: List[Dict[str, str]] = []
    
    clean_allergies = [a.strip().upper() for a in allergies]
    clean_meds = [m.strip().upper() for m in medications]

    for allergen in clean_allergies:
        for class_name, conflicting_drugs in CONTRAINDICATION_RULES.items():
            if class_name in allergen or allergen in class_name:
                for med in clean_meds:
                    for c_drug in conflicting_drugs:
                        if c_drug in med:
                            conflicts.append({
                                "allergen": allergen,
                                "prescribed_medication": med,
                                "drug_class": class_name,
                                "risk_level": "HIGH",
                                "warning": f"Cross-reactivity risk: Patient allergic to {allergen}, but taking {med}."
                            })

    return {
        "has_conflicts": len(conflicts) > 0,
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "safe_to_proceed": len(conflicts) == 0,
        "recommendation": (
            "SAFETY WARNING: Consult clinical pharmacist immediately before medication administration."
            if conflicts else "Medication and allergy cross-check clear. No immediate conflicts found."
        )
    }
