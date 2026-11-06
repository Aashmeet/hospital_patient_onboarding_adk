"""Longitudinal clinical memory and patient history retrieval."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ClinicalMemoryEntry(BaseModel):
    """Clinical note or historical episode stored for a patient."""
    mrn: str
    timestamp: str
    category: str = Field(description="Encounter, Allergy, MedicationChange, Diagnosis")
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)


class LongitudinalPatientMemory:
    """Stores and retrieves historical patient clinical context across visits."""

    def __init__(self) -> None:
        self._store: Dict[str, List[ClinicalMemoryEntry]] = {}

    def record_episode(
        self,
        mrn: str,
        category: str,
        summary: str,
        details: Optional[Dict[str, Any]] = None,
        timestamp: str = "2026-10-31T07:00:00Z"
    ) -> None:
        """Append a clinical event to the patient's longitudinal history."""
        if mrn not in self._store:
            self._store[mrn] = []
        
        self._store[mrn].append(
            ClinicalMemoryEntry(
                mrn=mrn,
                timestamp=timestamp,
                category=category,
                summary=summary,
                details=details or {}
            )
        )

    def retrieve_patient_history(self, mrn: str) -> List[Dict[str, Any]]:
        """Retrieve all recorded clinical memory entries for a given patient."""
        entries = self._store.get(mrn, [])
        return [e.model_dump() for e in entries]

    def query_recent_allergies(self, mrn: str) -> List[str]:
        """Extract all historically documented allergies from patient memory."""
        entries = self._store.get(mrn, [])
        allergies: List[str] = []
        for entry in entries:
            if entry.category == "Allergy":
                allergen = entry.details.get("allergen")
                if allergen and allergen not in allergies:
                    allergies.append(allergen)
        return allergies


# Global singleton instance for clinical memory retrieval
patient_memory_store = LongitudinalPatientMemory()
