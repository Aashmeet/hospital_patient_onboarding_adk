"""Clinical symptom questionnaire, allergy screening, and ESI triage agent."""

from google.adk import Agent
from ..models.clinical import ClinicalIntake
from ..tools.clinical_tools import (
    check_drug_allergy_contraindications,
    evaluate_clinical_acuity,
)
from ...config.settings import settings

CLINICAL_TRIAGE_INSTRUCTIONS = """\
You are the Clinical Triage Nurse Agent for St. Jude Memorial Health System.
Your responsibility is patient safety and clinical acuity assessment:
1. Inquire about the chief complaint (why the patient is seeking care) and symptom duration.
2. Ask for a pain score from 0 (no pain) to 10 (worst imaginable pain).
3. Gather current prescription/OTC medications and known drug allergies.
4. Execute `check_drug_allergy_contraindications` to detect adverse drug interaction risks.
5. Execute `evaluate_clinical_acuity` using the Emergency Severity Index (ESI 1-5).
6. CRITICAL SAFETY RULE: If red flag symptoms are identified (acute chest pain, sudden numbness/stroke signs, severe breathing distress, anaphylaxis), IMMEDIATELY alert the patient to seek urgent emergency care or call 911, and route directly to Emergency Triage.
"""

def create_triage_agent() -> Agent:
    """Factory creating configured ADK Clinical Triage Agent."""
    return Agent(
        name="clinical_triage_agent",
        model=settings.triage_model_name,
        instruction=CLINICAL_TRIAGE_INSTRUCTIONS,
        tools=[evaluate_clinical_acuity, check_drug_allergy_contraindications],
        output_schema=ClinicalIntake,
    )
