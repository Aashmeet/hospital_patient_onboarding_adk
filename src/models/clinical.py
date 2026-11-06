"""Clinical intake, medical history, and triage acuity models."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class AcuityLevel(str, Enum):
    """Emergency Severity Index (ESI) 5-level clinical triage classification."""
    ESI_1_RESUSCITATION = "ESI-1 (Immediate Resuscitation Required)"
    ESI_2_EMERGENT = "ESI-2 (Emergent / High Risk)"
    ESI_3_URGENT = "ESI-3 (Urgent / Multiple Resources)"
    ESI_4_LESS_URGENT = "ESI-4 (Less Urgent / One Resource)"
    ESI_5_NON_URGENT = "ESI-5 (Non-urgent / Primary Care)"


class Allergy(BaseModel):
    """Documented adverse drug or environmental reaction."""
    allergen: str = Field(..., description="Drug, substance, or food (e.g. Penicillin, Sulfa, Latex)")
    reaction: str = Field(..., description="Observed symptom: Anaphylaxis, Rash, Hives, GI Distress")
    severity: str = Field(default="Moderate", description="Mild, Moderate, Severe, Life-Threatening")


class Medication(BaseModel):
    """Active prescription or OTC medication."""
    drug_name: str = Field(..., description="Generic or brand name of medication (e.g. Lisinopril, Metformin)")
    dosage: str = Field(..., description="Dose amount with units (e.g. 10mg, 500mg)")
    frequency: str = Field(..., description="Administration frequency (e.g. Once daily, BID, PRN)")


class ClinicalIntake(BaseModel):
    """Patient clinical questionnaire and triage intake."""
    chief_complaint: str = Field(..., description="Primary reason for seeking hospital care")
    symptom_duration: str = Field(..., description="Duration of symptoms (e.g. 2 hours, 3 days, 2 weeks)")
    pain_score: int = Field(default=0, ge=0, le=10, description="Visual analog pain scale (0 to 10)")
    allergies: List[Allergy] = Field(default_factory=list, description="Documented patient allergies")
    medications: List[Medication] = Field(default_factory=list, description="Current home medications")
    chronic_conditions: List[str] = Field(default_factory=list, description="Past medical history (e.g. Hypertension, Diabetes)")
    red_flag_symptoms: List[str] = Field(
        default_factory=list,
        description="Critical red-flag symptoms: sudden chest pain, slurred speech, acute breathlessness"
    )
    assigned_acuity: Optional[AcuityLevel] = Field(
        default=None,
        description="Assigned Emergency Severity Index level"
    )
    recommended_department: Optional[str] = Field(
        default=None,
        description="Department best suited to manage patient"
    )
